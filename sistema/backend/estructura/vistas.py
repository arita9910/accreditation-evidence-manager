from django.db.models import Prefetch
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Criterio, CriterioModelo, Dimension, ModeloDefinicion, VersionNormativa
from .serializadores import (
    CriterioSerializador,
    DimensionSerializador,
    ModeloDefinicionSerializador,
    VersionNormativaSerializador,
)


def _version_activa():
    return VersionNormativa.objects.filter(activa=True).order_by(
        "-fecha_aprobacion", "-pk"
    ).first()


def _prefetch_modelos(ruta):
    return Prefetch(
        ruta,
        queryset=CriterioModelo.objects.select_related("modelo").order_by("modelo__numero"),
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def arbol_catalogo(request):
    version = _version_activa()
    if version is None:
        raise NotFound("No hay una versión activa.")
    dimensiones = (
        Dimension.objects.filter(version=version)
        .order_by("orden", "codigo")
        .prefetch_related(
            "indicadores__criterios__evidencias_sugeridas",
            "indicadores__criterios__requisitos_categoria",
            _prefetch_modelos("indicadores__criterios__modelos_relacionados"),
        )
    )
    return Response(
        {
            "version": VersionNormativaSerializador(version).data,
            "dimensiones": DimensionSerializador(dimensiones, many=True).data,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def ficha_criterio(request, codigo):
    version = _version_activa()
    criterio = (
        Criterio.objects.select_related("indicador__dimension__version")
        .prefetch_related(
            "evidencias_sugeridas",
            "requisitos_categoria",
            _prefetch_modelos("modelos_relacionados"),
        )
        .filter(indicador__dimension__version=version, codigo=codigo)
        .first()
    )
    if criterio is None:
        raise NotFound()
    return Response(CriterioSerializador(criterio).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def lista_modelos(request):
    version = _version_activa()
    if version is None:
        raise NotFound("No hay una versión activa.")
    modelos = (
        ModeloDefinicion.objects.filter(version=version)
        .order_by("numero")
        .prefetch_related("campos")
    )
    return Response(ModeloDefinicionSerializador(modelos, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def lista_versiones(request):
    versiones = VersionNormativa.objects.all().order_by("-fecha_aprobacion", "nombre")
    return Response(VersionNormativaSerializador(versiones, many=True).data)
