from __future__ import annotations

import re

from django.conf import settings
from django.db.models import Q

from ciclos.modelos import Ciclo
from estructura.models import Criterio, Dimension, Indicador

from .modelos import Evidencia


__all__ = ["buscar", "buscar_evidencias"]


def _motor_base_datos():
    motor = settings.DATABASES.get("default", {}).get("ENGINE", "")
    if "postgresql" in motor:
        return "postgresql"
    return "sqlite"


def _normalizar_id(valor):
    if valor in (None, ""):
        return None, False
    if isinstance(valor, bool):
        return None, True
    if isinstance(valor, int):
        return valor, False
    texto = str(valor).strip()
    if not texto:
        return None, False
    if not texto.isdigit():
        return None, True
    return int(texto), False


def _resolver_ciclo(ciclo):
    if ciclo in (None, ""):
        return None, False
    if hasattr(ciclo, "pk"):
        return ciclo, False
    ciclo_id, es_invalido = _normalizar_id(ciclo)
    if es_invalido or ciclo_id is None:
        return None, True
    try:
        return Ciclo.objects.get(pk=ciclo_id), False
    except Ciclo.DoesNotExist:
        return None, True


def buscar(ciclo=None, texto=None, filtros=None, queryset=None):
    ciclo_obj, ciclo_invalido = _resolver_ciclo(ciclo)
    filtros = dict(filtros or {})

    if queryset is None:
        queryset = Evidencia.objects.select_related(
            "ciclo__carrera",
            "tipo_evidencia__dimension",
        ).prefetch_related(
            "clasificaciones__criterio__indicador__dimension",
            "ficheros",
        )

    if ciclo_invalido:
        return queryset.none()

    if ciclo_obj is not None:
        queryset = queryset.filter(ciclo=ciclo_obj)

    termino = str(texto or filtros.get("texto") or filtros.get("q") or "").strip()
    if termino:
        suposicion = re.split(r"\s+", termino)
        condiciones = Q()
        for parte in suposicion:
            parte = parte.strip()
            if not parte:
                continue
            condiciones |= (
                Q(titulo__icontains=parte)
                | Q(descripcion__icontains=parte)
                | Q(ficheros__nombre_original__icontains=parte)
                | Q(clasificaciones__criterio__codigo__icontains=parte)
                | Q(clasificaciones__criterio__texto__icontains=parte)
            )
        queryset = queryset.filter(condiciones).distinct()

    dimension_id_raw = filtros.get("dimension") or filtros.get("dimension_id")
    dimension_id, dimension_invalida = _normalizar_id(dimension_id_raw)
    if dimension_invalida:
        return queryset.none()
    if dimension_id is not None:
        queryset = queryset.filter(
            Q(tipo_evidencia__dimension_id=dimension_id)
            | Q(clasificaciones__criterio__indicador__dimension_id=dimension_id)
        ).distinct()

    indicador_id_raw = filtros.get("indicador") or filtros.get("indicador_id")
    indicador_id, indicador_invalido = _normalizar_id(indicador_id_raw)
    if indicador_invalido:
        return queryset.none()
    if indicador_id is not None:
        queryset = queryset.filter(
            Q(tipo_evidencia__dimension__indicadores__id=indicador_id)
            | Q(clasificaciones__criterio__indicador_id=indicador_id)
        ).distinct()

    criterio_id_raw = filtros.get("criterio") or filtros.get("criterio_id")
    criterio_id, criterio_invalido = _normalizar_id(criterio_id_raw)
    if criterio_invalido:
        return queryset.none()
    if criterio_id is not None:
        queryset = queryset.filter(clasificaciones__criterio_id=criterio_id).distinct()

    curso_academico = filtros.get("curso") or filtros.get("curso_academico")
    if curso_academico not in (None, ""):
        queryset = queryset.filter(curso_academico=curso_academico)

    soporte = filtros.get("soporte")
    if soporte not in (None, ""):
        queryset = queryset.filter(soporte=soporte)

    tipo_evidencia_raw = filtros.get("tipo") or filtros.get("tipo_evidencia") or filtros.get("tipo_evidencia_id")
    tipo_evidencia, tipo_invalido = _normalizar_id(tipo_evidencia_raw)
    if tipo_invalido:
        return queryset.none()
    if tipo_evidencia is not None:
        queryset = queryset.filter(tipo_evidencia_id=tipo_evidencia)

    if _motor_base_datos() == "postgresql":
        try:
            from django.contrib.postgres.search import SearchQuery, SearchVector

            vector = SearchVector("titulo", weight="A") + SearchVector("descripcion", weight="B")
            if termino:
                queryset = queryset.annotate(search=vector).filter(search=SearchQuery(termino))
        except Exception:
            pass

    return queryset.order_by("-pk")


buscar_evidencias = buscar
