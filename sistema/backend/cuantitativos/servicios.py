from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction

from auditoria.servicios import registrar
from ciclos.modelos import Ciclo
from ciclos.servicios import exigir_ciclo_abierto
from cuentas.permisos import puede
from estructura.models import Criterio, ModeloCampo, ModeloDefinicion
from evidencias.modelos import Evidencia

from .models import ValorCriterio, ValorModelo, VinculoDato


def _resolver_ciclo(valor):
    if valor is None:
        raise ValidationError("Debe indicarse un ciclo válido.")
    if isinstance(valor, Ciclo):
        return valor
    return Ciclo.objects.select_related("carrera", "version_normativa").get(pk=valor)


def _resolver_modelo(valor):
    if valor is None:
        raise ValidationError("Debe indicarse un modelo válido.")
    if isinstance(valor, ModeloDefinicion):
        return valor
    return ModeloDefinicion.objects.select_related("version").get(pk=valor)


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
    return Evidencia.objects.select_related("ciclo", "tipo_evidencia").get(pk=valor)


def _resolver_dato(valor):
    if valor is None:
        raise ValidationError("Debe indicarse un dato válido.")
    if isinstance(valor, ValorModelo):
        return valor
    if isinstance(valor, ValorCriterio):
        return valor
    for modelo in (ValorModelo, ValorCriterio):
        try:
            return modelo.objects.select_related("ciclo").get(pk=valor)
        except modelo.DoesNotExist:
            continue
    raise ValidationError("No existe un dato cuantitativo con ese identificador.")


def _requiere_permiso_escritura(usuario, ciclo):
    if usuario is None:
        return
    if not (
        puede(usuario, "crear_valoracion", objeto=ciclo)
        or puede(usuario, "editar_valoracion", objeto=ciclo)
    ):
        raise ValidationError("El usuario no tiene permisos para modificar datos cuantitativos del ciclo.")


def _coerce_decimal(valor, nombre):
    if valor in (None, ""):
        return None
    try:
        return Decimal(str(valor))
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError(f"El campo '{nombre}' debe ser un número válido.")


def _coerce_texto(valor):
    if valor is None:
        return ""
    return str(valor)


def _valor_esperado_para_campo(campo, valores):
    if valores is None:
        return None
    if isinstance(valores, dict):
        valor = valores.get("valor", valores.get("value"))
        numerador = valores.get("numerador", valores.get("numerator"))
        denominador = valores.get("denominador", valores.get("denominator"))
        return valor, numerador, denominador
    if isinstance(valores, (list, tuple)) and len(valores) >= 3:
        return valores[0], valores[1], valores[2]
    return valores, None, None


def _normalizar_valor_campo(campo, valor, numerador=None, denominador=None):
    if campo.tipo_valor == ModeloCampo.TipoValor.TEXTO:
        return _coerce_texto(valor), None, None

    valor_decimal = _coerce_decimal(valor, campo.__str__()) if valor not in (None, "") else None
    numerador_decimal = _coerce_decimal(numerador, f"{campo} numerador") if numerador not in (None, "") else None
    denominador_decimal = _coerce_decimal(denominador, f"{campo} denominador") if denominador not in (None, "") else None

    if numerador_decimal is not None and denominador_decimal is not None:
        if denominador_decimal <= 0:
            raise ValidationError(f"El denominador de '{campo}' debe ser mayor que cero.")
        if valor_decimal is None:
            valor_decimal = (numerador_decimal / denominador_decimal) * Decimal("100")
    if valor_decimal is not None and valor_decimal < 0:
        raise ValidationError(f"El valor de '{campo}' no puede ser negativo.")
    if campo.tipo_valor == ModeloCampo.TipoValor.PORCENTAJE and valor_decimal is not None:
        if not (Decimal("0") <= valor_decimal <= Decimal("100")):
            raise ValidationError(f"El porcentaje de '{campo}' debe estar entre 0 y 100.")
    return valor_decimal, numerador_decimal, denominador_decimal


def _celdas_a_diccionario(celdas):
    if celdas is None:
        return {}
    if isinstance(celdas, dict):
        return celdas
    if hasattr(celdas, "items"):
        return dict(celdas.items())
    resultado = {}
    for entrada in celdas:
        if isinstance(entrada, dict):
            if "campo" in entrada:
                resultado[entrada["campo"]] = {k: v for k, v in entrada.items() if k != "campo"}
            elif "campo_id" in entrada:
                resultado[entrada["campo_id"]] = {k: v for k, v in entrada.items() if k not in {"campo_id", "campo"}}
            else:
                raise ValidationError("Cada celda debe indicar el campo al que pertenece.")
        else:
            raise ValidationError("El formato de celdas no es válido.")
    return resultado


def guardar_valores_modelo(ciclo, modelo, curso, celdas, usuario=None):
    ciclo = _resolver_ciclo(ciclo)
    modelo = _resolver_modelo(modelo)
    exigir_ciclo_abierto(ciclo)
    _requiere_permiso_escritura(usuario, ciclo)

    curso_num = int(curso)
    campos_por_id = {campo.pk: campo for campo in modelo.campos.select_related("modelo").all()}
    if not campos_por_id:
        raise ValidationError("El modelo no tiene campos definidos.")

    celdas_map = _celdas_a_diccionario(celdas)
    registros = []
    with transaction.atomic():
        for clave, valor_celda in celdas_map.items():
            if isinstance(clave, ModeloCampo):
                campo = clave
            else:
                campo_pk = int(clave)
                campo = campos_por_id.get(campo_pk)
                if campo is None:
                    raise ValidationError("La celda no pertenece al modelo indicado.")

            valor, numerador, denominador = _valor_esperado_para_campo(campo, valor_celda)
            valor_normalizado, numerador_norm, denominador_norm = _normalizar_valor_campo(
                campo,
                valor,
                numerador,
                denominador,
            )

            registro, _ = ValorModelo.objects.get_or_create(
                ciclo=ciclo,
                campo=campo,
                curso=curso_num,
            )
            registro.valor = valor_normalizado
            registro.numerador = numerador_norm
            registro.denominador = denominador_norm
            registro.full_clean()
            registro.save()
            registros.append(registro)
            registrar(
                "guardar_valores_modelo",
                usuario=usuario,
                entidad="ValorModelo",
                detalle={"id": registro.pk, "ciclo_id": ciclo.pk, "modelo_id": modelo.pk, "curso": curso_num},
            )

    return registros


def guardar_valor_criterio(
    ciclo,
    criterio,
    *,
    valor=None,
    numerador=None,
    denominador=None,
    curso=None,
    unidad="",
    observacion="",
    usuario=None,
):
    ciclo = _resolver_ciclo(ciclo)
    criterio = _resolver_criterio(criterio)
    exigir_ciclo_abierto(ciclo)
    _requiere_permiso_escritura(usuario, ciclo)

    if criterio.modelos_relacionados.exists():
        raise ValidationError("El criterio asociado a un modelo no admite valor propio.")
    if criterio.tipo_dato == Criterio.TipoDato.CUALITATIVO:
        raise ValidationError("Los criterios cualitativos no admiten valor cuantitativo.")

    valor_decimal = _coerce_decimal(valor, "valor") if valor not in (None, "") else None
    numerador_decimal = _coerce_decimal(numerador, "numerador") if numerador not in (None, "") else None
    denominador_decimal = _coerce_decimal(denominador, "denominador") if denominador not in (None, "") else None
    if numerador_decimal is not None and denominador_decimal is not None:
        if denominador_decimal <= 0:
            raise ValidationError("El denominador debe ser mayor que cero.")
        if valor_decimal is None:
            valor_decimal = (numerador_decimal / denominador_decimal) * Decimal("100")
    if valor_decimal is not None and valor_decimal < 0:
        raise ValidationError("El valor no puede ser negativo.")

    with transaction.atomic():
        registro, _ = ValorCriterio.objects.get_or_create(ciclo=ciclo, criterio=criterio)
        registro.curso = curso
        registro.valor = valor_decimal
        registro.numerador = numerador_decimal
        registro.denominador = denominador_decimal
        registro.unidad = str(unidad or "")
        registro.observacion = str(observacion or "")
        registro.full_clean()
        registro.save()
        registrar(
            "guardar_valor_criterio",
            usuario=usuario,
            entidad="ValorCriterio",
            detalle={"id": registro.pk, "ciclo_id": ciclo.pk, "criterio_id": criterio.pk},
        )
    return registro


def rellenar_acreditacion_anterior(ciclo):
    ciclo = _resolver_ciclo(ciclo)
    ciclo_anterior = ciclo.ciclo_anterior
    if ciclo_anterior is None:
        return []

    actualizados = []
    for dato in ValorModelo.objects.filter(ciclo=ciclo).select_related("campo", "campo__modelo"):
        previo = (
            ValorModelo.objects.filter(ciclo=ciclo_anterior, campo=dato.campo, curso=dato.curso)
            .order_by("pk")
            .first()
        )
        if previo is None or dato.valor is not None:
            continue
        dato.valor = previo.valor
        dato.numerador = previo.numerador
        dato.denominador = previo.denominador
        dato.save(update_fields=["valor", "numerador", "denominador"])
        actualizados.append(dato)

    for dato in ValorCriterio.objects.filter(ciclo=ciclo).select_related("criterio"):
        previo = ValorCriterio.objects.filter(ciclo=ciclo_anterior, criterio=dato.criterio).order_by("pk").first()
        if previo is None or dato.valor is not None:
            continue
        dato.valor = previo.valor
        dato.numerador = previo.numerador
        dato.denominador = previo.denominador
        dato.unidad = previo.unidad
        dato.observacion = previo.observacion
        dato.save(update_fields=["valor", "numerador", "denominador", "unidad", "observacion"])
        actualizados.append(dato)

    return actualizados


def datos_sin_respaldo(ciclo):
    ciclo = _resolver_ciclo(ciclo)
    return list(
        ValorModelo.objects.filter(ciclo=ciclo)
        .exclude(vinculos__isnull=False)
        .select_related("campo__modelo")
    ) + list(
        ValorCriterio.objects.filter(ciclo=ciclo)
        .exclude(vinculos__isnull=False)
        .select_related("criterio")
    )


def datos_de_evidencia(evidencia):
    evidencia = _resolver_evidencia(evidencia)
    resultados = []
    for enlace in VinculoDato.objects.filter(evidencia=evidencia).select_related(
        "valor_modelo__campo__modelo",
        "valor_criterio__criterio",
    ):
        if enlace.valor_modelo_id is not None:
            resultados.append(enlace.valor_modelo)
        elif enlace.valor_criterio_id is not None:
            resultados.append(enlace.valor_criterio)
    return resultados


def vincular(dato, evidencias, usuario=None):
    dato_obj = _resolver_dato(dato)
    ciclo = dato_obj.ciclo
    exigir_ciclo_abierto(ciclo)
    _requiere_permiso_escritura(usuario, ciclo)

    if isinstance(evidencias, (str, int, Evidencia)):
        evidencias = [evidencias]

    creados = []
    with transaction.atomic():
        for valor in evidencias:
            evidencia = _resolver_evidencia(valor)
            if evidencia.ciclo_id != ciclo.pk:
                raise ValidationError("La evidencia debe pertenecer al mismo ciclo que el dato.")
            if isinstance(dato_obj, ValorModelo):
                enlace = VinculoDato(
                    evidencia=evidencia,
                    valor_modelo=dato_obj,
                    valor_criterio=None,
                )
            else:
                enlace = VinculoDato(
                    evidencia=evidencia,
                    valor_modelo=None,
                    valor_criterio=dato_obj,
                )
            enlace.full_clean()
            if not VinculoDato.objects.filter(
                evidencia=evidencia,
                valor_modelo_id=enlace.valor_modelo_id,
                valor_criterio_id=enlace.valor_criterio_id,
            ).exists():
                enlace.save()
                creados.append(enlace)
                registrar(
                    "vincular_dato",
                    usuario=usuario,
                    entidad="VinculoDato",
                    detalle={
                        "evidencia_id": evidencia.pk,
                        "dato_tipo": "ValorModelo" if isinstance(dato_obj, ValorModelo) else "ValorCriterio",
                        "dato_id": dato_obj.pk,
                    },
                )
    return creados


def desvincular(dato, evidencias, usuario=None):
    dato_obj = _resolver_dato(dato)
    ciclo = dato_obj.ciclo
    exigir_ciclo_abierto(ciclo)
    _requiere_permiso_escritura(usuario, ciclo)

    if isinstance(evidencias, (str, int, Evidencia)):
        evidencias = [evidencias]

    eliminados = 0
    with transaction.atomic():
        for valor in evidencias:
            evidencia = _resolver_evidencia(valor)
            if evidencia.ciclo_id != ciclo.pk:
                raise ValidationError("La evidencia debe pertenecer al mismo ciclo que el dato.")
            queryset = VinculoDato.objects.filter(evidencia=evidencia)
            if isinstance(dato_obj, ValorModelo):
                queryset = queryset.filter(valor_modelo=dato_obj)
            else:
                queryset = queryset.filter(valor_criterio=dato_obj)
            total = queryset.delete()[0]
            eliminados += total
            if total:
                registrar(
                    "desvincular_dato",
                    usuario=usuario,
                    entidad="VinculoDato",
                    detalle={
                        "evidencia_id": evidencia.pk,
                        "dato_tipo": "ValorModelo" if isinstance(dato_obj, ValorModelo) else "ValorCriterio",
                        "dato_id": dato_obj.pk,
                        "eliminados": total,
                    },
                )
    return eliminados


__all__ = [
    "guardar_valores_modelo",
    "guardar_valor_criterio",
    "rellenar_acreditacion_anterior",
    "datos_sin_respaldo",
    "datos_de_evidencia",
    "vincular",
    "desvincular",
]
