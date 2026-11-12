from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import transaction

from auditoria.servicios import registrar
from ciclos.modelos import AsignacionDimension
from ciclos.servicios import exigir_ciclo_abierto
from cuentas.permisos import puede
from estructura.models import Criterio
from evidencias.modelos import Evidencia

from .models import Valoracion, ValoracionCriterio, ValoracionEvidencia


def _normalizar_tipo_valoracion(tipo):
    if tipo is None:
        raise ValidationError("Debe indicarse el tipo de valoración.")
    if isinstance(tipo, Valoracion.Tipo):
        return tipo.value
    valor = str(tipo).strip().lower()
    for opcion, _ in Valoracion.Tipo.choices:
        if opcion == valor:
            return opcion
    raise ValidationError("El tipo de valoración debe ser 'fortaleza' o 'debilidad'.")


def _resolver_criterio(valor):
    if valor is None:
        raise ValidationError("Debe indicarse un criterio válido.")
    if isinstance(valor, Criterio):
        return valor
    return Criterio.objects.select_related("indicador__dimension").get(pk=valor)


def _resolver_evidencia(valor):
    if valor is None:
        raise ValidationError("Debe indicarse una evidencia válida.")
    if isinstance(valor, Evidencia):
        return valor
    return Evidencia.objects.select_related("ciclo").get(pk=valor)


def _resolver_valoracion(valor):
    if valor is None:
        raise ValidationError("Debe indicarse una valoración válida.")
    if isinstance(valor, Valoracion):
        return valor
    return Valoracion.objects.select_related("ciclo", "dimension", "redactada_por").get(pk=valor)


def _puede_operar_dimension(actor, accion, ciclo, dimension):
    if actor is None:
        return False
    if puede(actor, accion, objeto=ciclo):
        return True
    if ciclo is None or dimension is None:
        return False
    return AsignacionDimension.objects.filter(
        ciclo=ciclo,
        usuario=actor,
        dimension=dimension,
    ).exists()


def _validar_criterios_y_evidencias(ciclo, dimension, criterios, evidencias):
    criterios_validos = []
    ids_criterios = set()
    for criterio in criterios or []:
        criterio_obj = _resolver_criterio(criterio)
        if criterio_obj.indicador.dimension_id != dimension.pk:
            raise ValidationError(
                "El criterio debe pertenecer a la misma dimensión de la valoración."
            )
        if criterio_obj.indicador.dimension.version_id != ciclo.version_normativa_id:
            raise ValidationError(
                "El criterio debe pertenecer a la misma versión normativa del ciclo."
            )
        # VERSIÓN VIVA: vinculamos el criterio por su ID actual del catálogo para respetar
        # la versión normativa del ciclo. Si más adelante se exige inmutabilidad estricta,
        # habrá que añadir un campo JSON con el snapshot del criterio en el momento de la valoración.
        if criterio_obj.pk not in ids_criterios:
            criterios_validos.append(criterio_obj)
            ids_criterios.add(criterio_obj.pk)

    evidencias_validas = []
    ids_evidencias = set()
    for evidencia in evidencias or []:
        evidencia_obj = _resolver_evidencia(evidencia)
        if evidencia_obj.ciclo_id != ciclo.pk:
            raise ValidationError(
                "La evidencia debe pertenecer al mismo ciclo que la valoración."
            )
        if evidencia_obj.pk not in ids_evidencias:
            evidencias_validas.append(evidencia_obj)
            ids_evidencias.add(evidencia_obj.pk)

    if not criterios_validos:
        raise ValidationError("Debe incluir al menos un criterio válido en la valoración.")
    if not evidencias_validas:
        raise ValidationError("Debe incluir al menos una evidencia válida en la valoración.")

    return criterios_validos, evidencias_validas


def _depende_de_acciones_mejora(valoracion):
    for model in apps.get_models():
        if model in (Valoracion, ValoracionCriterio, ValoracionEvidencia):
            continue
        for field in model._meta.get_fields():
            if not getattr(field, "is_relation", False):
                continue
            if not getattr(field, "concrete", False):
                continue
            related_model = getattr(field, "remote_field", None)
            if related_model is None:
                continue
            if getattr(related_model, "model", None) is not Valoracion:
                continue
            fk_name = field.name
            if getattr(model.objects.filter(**{fk_name: valoracion}).first(), "pk", None) is not None:
                return model
    return None


def crear_valoracion(ciclo, dimension, tipo, texto, criterios, evidencias, usuario=None, **kwargs):
    if ciclo is None:
        raise ValidationError("Debe indicar un ciclo válido.")
    exigir_ciclo_abierto(ciclo)
    if dimension is None:
        raise ValidationError("Debe indicarse una dimensión válida.")
    if not _puede_operar_dimension(usuario, "crear_valoracion", ciclo, dimension):
        raise ValidationError("El usuario no tiene permisos para crear valoraciones en esta dimensión.")

    tipo_valoracion = _normalizar_tipo_valoracion(tipo)
    texto_limpio = (texto or "").strip()
    if not texto_limpio:
        raise ValidationError("El texto de la valoración es obligatorio.")

    criterios_validos, evidencias_validas = _validar_criterios_y_evidencias(
        ciclo,
        dimension,
        criterios,
        evidencias,
    )

    with transaction.atomic():
        valoracion = Valoracion.objects.create(
            ciclo=ciclo,
            dimension=dimension,
            tipo=tipo_valoracion,
            texto=texto_limpio,
            redactada_por=usuario,
        )
        ValoracionCriterio.objects.bulk_create(
            [
                ValoracionCriterio(valoracion=valoracion, criterio=criterio)
                for criterio in criterios_validos
            ]
        )
        ValoracionEvidencia.objects.bulk_create(
            [
                ValoracionEvidencia(valoracion=valoracion, evidencia=evidencia)
                for evidencia in evidencias_validas
            ]
        )
        registrar(
            "crear_valoracion",
            usuario=usuario,
            entidad="Valoracion",
            detalle={
                "id": valoracion.pk,
                "ciclo_id": ciclo.pk,
                "dimension_id": dimension.pk,
                "tipo": tipo_valoracion,
            },
        )
    return valoracion


def editar_valoracion(
    valoracion,
    *,
    dimension=None,
    tipo=None,
    texto=None,
    criterios=None,
    evidencias=None,
    usuario=None,
    **kwargs,
):
    valoracion = _resolver_valoracion(valoracion)
    ciclo = valoracion.ciclo
    exigir_ciclo_abierto(ciclo)

    dimension_obj = dimension or valoracion.dimension
    if not _puede_operar_dimension(usuario, "editar_valoracion", ciclo, dimension_obj):
        raise ValidationError("El usuario no tiene permisos para editar esta valoración.")

    if tipo is not None:
        valoracion.tipo = _normalizar_tipo_valoracion(tipo)
    if texto is not None:
        valoracion.texto = (texto or "").strip()
        if not valoracion.texto:
            raise ValidationError("El texto de la valoración es obligatorio.")
    if dimension is not None:
        if dimension.version_id != ciclo.version_normativa_id:
            raise ValidationError("La dimensión debe pertenecer a la misma versión normativa del ciclo.")
        valoracion.dimension = dimension

    if criterios is not None or evidencias is not None:
        criterios_obj = criterios if criterios is not None else [rel.criterio for rel in valoracion.criterios.select_related("criterio")]
        evidencias_obj = evidencias if evidencias is not None else [rel.evidencia for rel in valoracion.evidencias.select_related("evidencia")]
        criterios_validos, evidencias_validas = _validar_criterios_y_evidencias(
            ciclo,
            valoracion.dimension,
            criterios_obj,
            evidencias_obj,
        )
    else:
        criterios_validos = None
        evidencias_validas = None

    with transaction.atomic():
        valoracion.save()
        if criterios is not None:
            ValoracionCriterio.objects.filter(valoracion=valoracion).delete()
            ValoracionCriterio.objects.bulk_create(
                [
                    ValoracionCriterio(valoracion=valoracion, criterio=criterio)
                    for criterio in criterios_validos
                ]
            )
        if evidencias is not None:
            ValoracionEvidencia.objects.filter(valoracion=valoracion).delete()
            ValoracionEvidencia.objects.bulk_create(
                [
                    ValoracionEvidencia(valoracion=valoracion, evidencia=evidencia)
                    for evidencia in evidencias_validas
                ]
            )
        registrar(
            "editar_valoracion",
            usuario=usuario,
            entidad="Valoracion",
            detalle={
                "id": valoracion.pk,
                "tipo": valoracion.tipo,
                "dimension_id": valoracion.dimension_id,
            },
        )
    return valoracion


def eliminar_valoracion(valoracion, usuario=None, **kwargs):
    valoracion = _resolver_valoracion(valoracion)
    exigir_ciclo_abierto(valoracion.ciclo)
    if not _puede_operar_dimension(usuario, "eliminar_valoracion", valoracion.ciclo, valoracion.dimension):
        raise ValidationError("El usuario no tiene permisos para eliminar esta valoración.")

    dependencia = _depende_de_acciones_mejora(valoracion)
    if dependencia is not None:
        raise ValidationError(
            "No se puede eliminar la valoración porque tiene acciones de mejora asociadas."
        )

    with transaction.atomic():
        detalle = {
            "id": valoracion.pk,
            "tipo": valoracion.tipo,
            "ciclo_id": valoracion.ciclo_id,
            "dimension_id": valoracion.dimension_id,
        }
        valoracion.delete()
        registrar(
            "eliminar_valoracion",
            usuario=usuario,
            entidad="Valoracion",
            detalle=detalle,
        )
    return True


def formatear_porcentaje(numerador, denominador):
    try:
        numerador_dec = Decimal(str(numerador))
        denominador_dec = Decimal(str(denominador))
    except (InvalidOperation, ValueError):
        raise ValidationError("El numerador y el denominador deben ser valores numéricos.")

    if denominador_dec == 0:
        raise ValidationError("El denominador no puede ser cero.")

    porcentaje = (numerador_dec / denominador_dec) * Decimal("100")
    porcentaje_redondeado = porcentaje.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    texto_porcentaje = f"{porcentaje_redondeado:.1f}".replace(".", ",")
    return f"{texto_porcentaje} % ({numerador}/{denominador})"


__all__ = [
    "crear_valoracion",
    "editar_valoracion",
    "eliminar_valoracion",
    "formatear_porcentaje",
]
