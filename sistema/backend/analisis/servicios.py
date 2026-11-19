from django.core.exceptions import ValidationError

from auditoria.servicios import registrar
from cuentas.permisos import puede
from ciclos.modelos import Ciclo
from cuantitativos.models import ValorCriterio, ValorModelo
from cuantitativos.servicios import datos_sin_respaldo
from estructura.models import (
    Criterio,
    Dimension,
    ModeloCampo,
)
from evidencias.modelos import Clasificacion
from valoracion.models import Valoracion

from .estructuras import (
    ComparacionPayload,
    CompletitudPayload,
    CriterioEstado,
    DimensionEstado,
    EstadoCicloPayload,
    IndicadorEstado,
)


_SIN_USUARIO = object()


def _resolver_ciclo(ciclo):
    if isinstance(ciclo, Ciclo):
        return ciclo
    if not isinstance(ciclo, (int, str)):
        raise ValidationError("Debe indicarse un ciclo válido.")
    try:
        return Ciclo.objects.select_related("carrera", "version_normativa").get(pk=int(ciclo))
    except (Ciclo.DoesNotExist, TypeError, ValueError):
        raise ValidationError("El ciclo no existe.")


def _requerir_permiso(actor, accion, objeto=None):
    if actor is _SIN_USUARIO:
        return
    if actor is None:
        raise ValidationError("Se requiere una sesión autenticada.")
    if not puede(actor, accion, objeto=objeto):
        raise ValidationError("No tiene permiso para realizar esta acción.")


def _tiene_dato(valor):
    if valor is None:
        return False
    return (
        getattr(valor, "valor", None) is not None
        or getattr(valor, "numerador", None) is not None
        or getattr(valor, "denominador", None) is not None
    )


def estado_ciclo(ciclo, usuario=_SIN_USUARIO):
    ciclo = _resolver_ciclo(ciclo)
    _requerir_permiso(usuario, "consultar_estado_analisis", objeto=ciclo)

    dimensiones = (
        Dimension.objects.filter(version=ciclo.version_normativa)
        .prefetch_related("indicadores", "indicadores__criterios")
        .order_by("orden", "pk")
    )

    clasificaciones = Clasificacion.objects.filter(
        evidencia__ciclo=ciclo
    ).values_list("criterio_id", flat=True)
    evidencias_por_criterio = {}
    for criterio_id in clasificaciones:
        evidencias_por_criterio[criterio_id] = (
            evidencias_por_criterio.get(criterio_id, 0) + 1
        )

    valores_modelo = (
        ValorModelo.objects.filter(ciclo=ciclo)
        .select_related("campo", "campo__modelo")
        .prefetch_related("vinculos")
    )
    valores_por_campo = {}
    respaldo_por_campo_curso = set()
    for valor in valores_modelo:
        clave = (valor.campo_id, valor.curso)
        valores_por_campo[clave] = valor
        if valor.vinculos.exists():
            respaldo_por_campo_curso.add(clave)

    valores_criterio = (
        ValorCriterio.objects.filter(ciclo=ciclo)
        .select_related("criterio")
        .prefetch_related("vinculos")
    )
    respaldo_criterios = {
        valor.criterio_id
        for valor in valores_criterio
        if valor.vinculos.exists()
    }
    valores_por_criterio = {valor.criterio_id: valor for valor in valores_criterio}

    valoraciones = (
        Valoracion.objects.filter(ciclo=ciclo)
        .select_related("dimension")
        .prefetch_related("criterios", "acciones_mejora")
    )
    valoracion_criterios = set()
    accion_criterios = set()
    for valoracion in valoraciones:
        if valoracion.tipo == Valoracion.Tipo.DEBILIDAD:
            for accion in valoracion.acciones_mejora.all():
                if accion.pk:
                    for criterio_relacion in valoracion.criterios.all():
                        accion_criterios.add(criterio_relacion.criterio_id)
        for criterio_relacion in valoracion.criterios.all():
            valoracion_criterios.add(criterio_relacion.criterio_id)

    modelos_por_criterio = {}
    relaciones = Criterio.objects.filter(
        indicador__dimension__version=ciclo.version_normativa
    ).prefetch_related("modelos_relacionados")
    for criterio in relaciones:
        modelos_por_criterio[criterio.pk] = {
            relacion.modelo_id for relacion in criterio.modelos_relacionados.all()
        }

    campos_por_modelo = {}
    for campo in ModeloCampo.objects.filter(
        modelo__version=ciclo.version_normativa
    ).values_list("pk", "modelo_id"):
        campos_por_modelo.setdefault(campo[1], set()).add(campo[0])

    dimensiones_payload = []
    for dimension in dimensiones:
        indicadores_payload = []
        for indicador in dimension.indicadores.all().order_by("pk"):
            criterios_payload = []
            for criterio in indicador.criterios.all().order_by("pk"):
                modelo_ids = modelos_por_criterio.get(criterio.pk, set())
                datos_cuantitativos = bool(
                    modelo_ids
                    and any(
                        (campo_id, curso) in valores_por_campo
                        for campo_id in {
                            campo_id
                            for modelo_id in modelo_ids
                            for campo_id in campos_por_modelo.get(modelo_id, set())
                        }
                        for curso in range(ciclo.curso_inicial, ciclo.curso_final + 1)
                    )
                ) or criterio.pk in valores_por_criterio

                dato_con_respaldo = False
                if modelo_ids:
                    dato_con_respaldo = any(
                        (campo_id, curso) in respaldo_por_campo_curso
                        for campo_id in {
                            campo_id
                            for modelo_id in modelo_ids
                            for campo_id in campos_por_modelo.get(modelo_id, set())
                        }
                        for curso in range(ciclo.curso_inicial, ciclo.curso_final + 1)
                    )
                elif criterio.pk in respaldo_criterios:
                    dato_con_respaldo = True

                criterios_payload.append(
                    CriterioEstado(
                        id=criterio.pk,
                        codigo=criterio.codigo,
                        nombre=criterio.texto,
                        evidencias_clasificadas=evidencias_por_criterio.get(criterio.pk, 0),
                        datos_cuantitativos=datos_cuantitativos,
                        dato_con_respaldo=dato_con_respaldo,
                        tiene_valoracion=criterio.pk in valoracion_criterios,
                        tiene_accion=criterio.pk in accion_criterios,
                    )
                )
            indicadores_payload.append(
                IndicadorEstado(
                    id=indicador.pk,
                    codigo=indicador.codigo,
                    nombre=indicador.texto,
                    criterios=tuple(criterios_payload),
                )
            )
        dimensiones_payload.append(
            DimensionEstado(
                id=dimension.pk,
                codigo=dimension.codigo,
                nombre=dimension.nombre,
                indicadores=tuple(indicadores_payload),
            )
        )

    return EstadoCicloPayload(
        ciclo_id=ciclo.pk,
        dimensiones=tuple(dimensiones_payload),
    )


def completitud(ciclo, usuario=_SIN_USUARIO):
    ciclo = _resolver_ciclo(ciclo)
    _requerir_permiso(usuario, "consultar_completitud_analisis", objeto=ciclo)

    criterios = (
        Criterio.objects.filter(indicador__dimension__version=ciclo.version_normativa)
        .select_related("indicador", "indicador__dimension")
        .prefetch_related("modelos_relacionados", "modelos_relacionados__modelo")
        .order_by("pk")
    )
    clasificados = set(
        Clasificacion.objects.filter(evidencia__ciclo=ciclo)
        .values_list("criterio_id", flat=True)
    )

    criterios_sin_evidencia = [
        criterio.pk for criterio in criterios if criterio.pk not in clasificados
    ]

    valores_modelo = list(
        ValorModelo.objects.filter(ciclo=ciclo).select_related("campo", "campo__modelo")
    )
    valores_por_modelo_campo_curso = {
        (valor.campo.modelo_id, valor.campo_id, valor.curso): valor
        for valor in valores_modelo
    }
    valores_criterio = {
        valor.criterio_id: valor
        for valor in ValorCriterio.objects.filter(ciclo=ciclo)
    }
    campos_por_modelo = {}
    for campo in ModeloCampo.objects.filter(
        modelo__version=ciclo.version_normativa
    ).order_by("modelo_id", "fila", "columna", "pk"):
        campos_por_modelo.setdefault(campo.modelo_id, []).append(campo)

    criterios_cuantitativos_sin_dato = []
    modelos_incompletos = []
    for criterio in criterios:
        modelo_ids = {
            relacion.modelo_id for relacion in criterio.modelos_relacionados.all()
        }
        if modelo_ids:
            tiene_dato = False
            for modelo_id in modelo_ids:
                campos = campos_por_modelo.get(modelo_id, [])
                for posicion in range(ciclo.curso_final - ciclo.curso_inicial + 1):
                    curso = ciclo.curso_inicial + posicion
                    presentes = sum(
                        1
                        for campo in campos
                        if _tiene_dato(
                            valores_por_modelo_campo_curso.get(
                                (modelo_id, campo.pk, curso)
                            )
                        )
                    )
                    if presentes:
                        tiene_dato = True
                    if presentes < len(campos):
                        modelos_incompletos.append(
                            {
                                "modelo_id": modelo_id,
                                "curso": curso,
                                "posicion_relativa": posicion,
                                "campos_esperados": len(campos),
                                "campos_presentes": presentes,
                            }
                        )
            if not tiene_dato:
                criterios_cuantitativos_sin_dato.append(criterio.pk)
        elif criterio.tipo_dato == Criterio.TipoDato.CUANTITATIVO:
            valor = valores_criterio.get(criterio.pk)
            if not _tiene_dato(valor):
                criterios_cuantitativos_sin_dato.append(criterio.pk)

    sin_respaldo = datos_sin_respaldo(ciclo)
    datos_sin_respaldo_payload = []
    for dato in sin_respaldo:
        if isinstance(dato, ValorModelo):
            datos_sin_respaldo_payload.append(
                {
                    "tipo": "valor_modelo",
                    "id": dato.pk,
                    "campo_id": dato.campo_id,
                    "modelo_id": dato.campo.modelo_id,
                    "curso": dato.curso,
                }
            )
        else:
            datos_sin_respaldo_payload.append(
                {
                    "tipo": "valor_criterio",
                    "id": dato.pk,
                    "criterio_id": dato.criterio_id,
                    "curso": dato.curso,
                }
            )

    valoraciones = (
        Valoracion.objects.filter(ciclo=ciclo)
        .select_related("dimension")
        .prefetch_related("criterios", "acciones_mejora")
    )
    dimensiones_con_valoracion = set(
        valoracion.dimension_id
        for valoracion in valoraciones
    )
    dimensiones_sin_valoracion = [
        dimension.pk
        for dimension in Dimension.objects.filter(
            version=ciclo.version_normativa
        ).order_by("pk")
        if dimension.pk not in dimensiones_con_valoracion
    ]

    debilidades_sin_accion = []
    for valoracion in valoraciones:
        if (
            valoracion.tipo == Valoracion.Tipo.DEBILIDAD
            and not valoracion.acciones_mejora.exists()
        ):
            debilidades_sin_accion.append(valoracion.pk)

    return CompletitudPayload(
        ciclo_id=ciclo.pk,
        criterios_sin_evidencia=tuple(criterios_sin_evidencia),
        criterios_cuantitativos_sin_dato=tuple(
            criterios_cuantitativos_sin_dato
        ),
        datos_sin_respaldo=tuple(datos_sin_respaldo_payload),
        modelos_incompletos=tuple(modelos_incompletos),
        dimensiones_sin_valoracion=tuple(dimensiones_sin_valoracion),
        debilidades_sin_accion=tuple(debilidades_sin_accion),
    )


def _normalizar_valor(valor):
    return {
        "valor": getattr(valor, "valor", None),
        "numerador": getattr(valor, "numerador", None),
        "denominador": getattr(valor, "denominador", None),
    }


def comparar(ciclo_a, ciclo_b, usuario=_SIN_USUARIO):
    ciclo_a = _resolver_ciclo(ciclo_a)
    ciclo_b = _resolver_ciclo(ciclo_b)

    if ciclo_a.carrera_id != ciclo_b.carrera_id:
        raise ValidationError("Los ciclos deben pertenecer a la misma carrera.")
    if ciclo_a.pk == ciclo_b.pk:
        raise ValidationError("Debe comparar dos ciclos distintos.")

    _requerir_permiso(usuario, "comparar_ciclos", objeto=ciclo_a)
    if usuario is not _SIN_USUARIO:
        if not puede(usuario, "comparar_ciclos", objeto=ciclo_b):
            raise ValidationError("No tiene permiso para realizar esta acción.")

    modelos_a = {
        (valor.campo_id, valor.curso - ciclo_a.curso_inicial): valor
        for valor in ValorModelo.objects.filter(ciclo=ciclo_a).select_related("campo")
    }
    modelos_b = {
        (valor.campo_id, valor.curso - ciclo_b.curso_inicial): valor
        for valor in ValorModelo.objects.filter(ciclo=ciclo_b).select_related("campo")
    }

    diferencias_modelos = []
    for clave in sorted(set(modelos_a) | set(modelos_b)):
        campo_id, posicion = clave
        valor_a = modelos_a.get(clave)
        valor_b = modelos_b.get(clave)
        diferencia_a = _normalizar_valor(valor_a)
        diferencia_b = _normalizar_valor(valor_b)
        if diferencia_a != diferencia_b:
            diferencias_modelos.append(
                {
                    "campo_id": campo_id,
                    "posicion_relativa": posicion,
                    "curso_a": ciclo_a.curso_inicial + posicion,
                    "curso_b": ciclo_b.curso_inicial + posicion,
                    "valor_a": diferencia_a["valor"],
                    "valor_b": diferencia_b["valor"],
                    "numerador_a": diferencia_a["numerador"],
                    "numerador_b": diferencia_b["numerador"],
                    "denominador_a": diferencia_a["denominador"],
                    "denominador_b": diferencia_b["denominador"],
                }
            )

    criterios_a = {
        valor.criterio_id: valor
        for valor in ValorCriterio.objects.filter(ciclo=ciclo_a)
    }
    criterios_b = {
        valor.criterio_id: valor
        for valor in ValorCriterio.objects.filter(ciclo=ciclo_b)
    }
    diferencias_criterios = []
    for criterio_id in sorted(set(criterios_a) | set(criterios_b)):
        valor_a = criterios_a.get(criterio_id)
        valor_b = criterios_b.get(criterio_id)
        if _normalizar_valor(valor_a) != _normalizar_valor(valor_b):
            diferencias_criterios.append(
                {
                    "criterio_id": criterio_id,
                    "valor_a": getattr(valor_a, "valor", None),
                    "valor_b": getattr(valor_b, "valor", None),
                    "numerador_a": getattr(valor_a, "numerador", None),
                    "numerador_b": getattr(valor_b, "numerador", None),
                    "denominador_a": getattr(valor_a, "denominador", None),
                    "denominador_b": getattr(valor_b, "denominador", None),
                    "unidad_a": getattr(valor_a, "unidad", ""),
                    "unidad_b": getattr(valor_b, "unidad", ""),
                }
            )

    def debilidades_por_clave(ciclo):
        agrupadas = {}
        valoraciones = (
            Valoracion.objects.filter(ciclo=ciclo, tipo=Valoracion.Tipo.DEBILIDAD)
            .prefetch_related("criterios", "acciones_mejora")
        )
        for valoracion in valoraciones:
            criterios_ids = sorted(
                relacion.criterio_id
                for relacion in valoracion.criterios.all()
            )
            clave = ("criterios", tuple(criterios_ids)) if criterios_ids else (
                "dimension",
                valoracion.dimension_id,
            )
            acciones = list(valoracion.acciones_mejora.all())
            estados = sorted({accion.estado for accion in acciones})
            agrupadas.setdefault(clave, []).append(
                (valoracion.pk, estados, len(acciones))
            )
        return agrupadas

    acciones_a = debilidades_por_clave(ciclo_a)
    acciones_b = debilidades_por_clave(ciclo_b)
    diferencias_acciones = []
    for clave in sorted(set(acciones_a) | set(acciones_b), key=lambda item: (item[0], str(item[1]))):
        registros_a = acciones_a.get(clave, [])
        registros_b = acciones_b.get(clave, [])
        estados_a = sorted({estado for _, estados, _ in registros_a for estado in estados})
        estados_b = sorted({estado for _, estados, _ in registros_b for estado in estados})
        total_a = sum(total for _, _, total in registros_a)
        total_b = sum(total for _, _, total in registros_b)
        if estados_a != estados_b or total_a != total_b:
            debilidad_id = (
                registros_a[0][0]
                if registros_a
                else registros_b[0][0] if registros_b else None
            )
            diferencias_acciones.append(
                {
                    "debilidad_id": debilidad_id,
                    "estado_a": estados_a[0] if len(estados_a) == 1 else estados_a,
                    "estado_b": estados_b[0] if len(estados_b) == 1 else estados_b,
                    "total_a": total_a,
                    "total_b": total_b,
                }
            )

    payload = ComparacionPayload(
        ciclo_a_id=ciclo_a.pk,
        ciclo_b_id=ciclo_b.pk,
        diferencias_modelos=tuple(diferencias_modelos),
        diferencias_criterios=tuple(diferencias_criterios),
        diferencias_acciones=tuple(diferencias_acciones),
    )

    if usuario is not _SIN_USUARIO:
        registrar(
            "comparar_ciclos",
            usuario=usuario,
            entidad="Ciclo",
            detalle={
                "ciclo_a_id": ciclo_a.pk,
                "ciclo_b_id": ciclo_b.pk,
            },
            contexto={
                "carrera_id": ciclo_a.carrera_id,
                "diferencias_modelos": len(diferencias_modelos),
                "diferencias_criterios": len(diferencias_criterios),
                "diferencias_acciones": len(diferencias_acciones),
            },
        )

    return payload
