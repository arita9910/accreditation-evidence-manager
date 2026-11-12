from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ciclos.modelos import AsignacionDimension, Ciclo
from cuentas.permisos import PermisoSistema, puede
from estructura.models import Dimension

from .models import Valoracion
from .serializadores import (
    ValoracionActualizarSerializador,
    ValoracionCrearSerializador,
    ValoracionSerializador,
)
from .servicios import eliminar_valoracion


def _puede_operar_dimension(usuario, accion, ciclo, dimension=None):
    if usuario is None or not getattr(usuario, "is_authenticated", False):
        return False
    if puede(usuario, accion, objeto=ciclo):
        return True
    if ciclo is None or dimension is None:
        return False
    return AsignacionDimension.objects.filter(
        ciclo=ciclo,
        usuario=usuario,
        dimension=dimension,
    ).exists()


def _es_visible_para_usuario(usuario, valoracion):
    if usuario is None or not getattr(usuario, "is_authenticated", False):
        return False
    if puede(usuario, "crear_valoracion", objeto=valoracion.ciclo):
        return True
    return AsignacionDimension.objects.filter(
        ciclo=valoracion.ciclo,
        usuario=usuario,
        dimension=valoracion.dimension,
    ).exists()


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="dimension",
            type=int,
            location=OpenApiParameter.QUERY,
            required=False,
        ),
        OpenApiParameter(
            name="tipo",
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
        ),
    ],
    responses={200: ValoracionSerializador(many=True), 201: ValoracionSerializador()},
)
class ValoracionesCicloVista(generics.ListCreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ValoracionSerializador

    def get_ciclo(self):
        return get_object_or_404(Ciclo.objects.all(), pk=self.kwargs["pk"])

    def get_queryset(self):
        ciclo = self.get_ciclo()
        usuario = getattr(self.request, "user", None)
        queryset = (
            Valoracion.objects.filter(ciclo=ciclo)
            .select_related("ciclo", "dimension", "redactada_por")
            .prefetch_related("criterios__criterio", "evidencias__evidencia")
            .order_by("pk")
        )
        if usuario is None or not getattr(usuario, "is_authenticated", False):
            return queryset.none()
        if puede(usuario, "crear_valoracion", objeto=ciclo):
            base_queryset = queryset
        else:
            base_queryset = queryset.filter(
                dimension__in=Dimension.objects.filter(
                    asignaciones__ciclo=ciclo,
                    asignaciones__usuario=usuario,
                ).distinct()
            )

        dimension_id = self.request.query_params.get("dimension") or self.request.query_params.get("dimension_id")
        if dimension_id not in (None, ""):
            base_queryset = base_queryset.filter(dimension_id=dimension_id)

        tipo = self.request.query_params.get("tipo")
        if tipo not in (None, ""):
            base_queryset = base_queryset.filter(tipo=tipo)

        return base_queryset

    def post(self, request, *args, **kwargs):
        ciclo = self.get_ciclo()
        serializer = ValoracionCrearSerializador(
            data=request.data,
            context={"request": request, "ciclo": ciclo},
        )
        serializer.is_valid(raise_exception=True)
        dimension = serializer.validated_data["dimension"]
        if not _puede_operar_dimension(request.user, "crear_valoracion", ciclo, dimension):
            raise PermisoSistema(
                "No tiene permiso para crear valoraciones en esta dimensión.",
                accion="crear_valoracion",
                entidad="Valoracion",
            )
        valoracion = serializer.save()
        return Response(ValoracionSerializador(valoracion).data, status=status.HTTP_201_CREATED)


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="dimension",
            type=int,
            location=OpenApiParameter.QUERY,
            required=False,
        ),
        OpenApiParameter(
            name="tipo",
            type=str,
            location=OpenApiParameter.QUERY,
            required=False,
        ),
    ],
    responses={200: ValoracionSerializador(many=True)},
)
class ValoracionDetalleVista(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ValoracionSerializador

    def get_queryset(self):
        queryset = (
            Valoracion.objects.select_related("ciclo", "dimension", "redactada_por")
            .prefetch_related("criterios__criterio", "evidencias__evidencia")
            .order_by("pk")
        )
        usuario = getattr(self.request, "user", None)
        if usuario is None or not getattr(usuario, "is_authenticated", False):
            return queryset.none()
        if puede(usuario, "crear_valoracion", objeto=None):
            return queryset
        return queryset.filter(
            dimension__in=Dimension.objects.filter(
                asignaciones__usuario=usuario,
            ).distinct()
        )

    def get_object(self):
        queryset = self.get_queryset()
        obj = queryset.filter(pk=self.kwargs["pk"]).first()
        if obj is None:
            raise NotFound()
        return obj

    def get(self, request, *args, **kwargs):
        valoracion = self.get_object()
        if not _es_visible_para_usuario(request.user, valoracion):
            raise NotFound()
        return Response(ValoracionSerializador(valoracion).data)

    def patch(self, request, *args, **kwargs):
        valoracion = self.get_object()
        if not _es_visible_para_usuario(request.user, valoracion):
            raise NotFound()
        serializer = ValoracionActualizarSerializador(
            data=request.data,
            partial=True,
            context={"request": request, "valoracion": valoracion},
        )
        serializer.is_valid(raise_exception=True)
        dimension = serializer.validated_data.get("dimension", valoracion.dimension)
        if not _puede_operar_dimension(request.user, "editar_valoracion", valoracion.ciclo, dimension):
            raise PermisoSistema(
                "No tiene permiso para editar esta valoración.",
                accion="editar_valoracion",
                entidad="Valoracion",
            )
        valoracion = serializer.save()
        return Response(ValoracionSerializador(valoracion).data)

    def delete(self, request, *args, **kwargs):
        valoracion = self.get_object()
        if not _es_visible_para_usuario(request.user, valoracion):
            raise NotFound()
        if not _puede_operar_dimension(request.user, "eliminar_valoracion", valoracion.ciclo, valoracion.dimension):
            raise PermisoSistema(
                "No tiene permiso para eliminar esta valoración.",
                accion="eliminar_valoracion",
                entidad="Valoracion",
            )
        eliminar_valoracion(valoracion, usuario=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


__all__ = [
    "ValoracionesCicloVista",
    "ValoracionDetalleVista",
]
