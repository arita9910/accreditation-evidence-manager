from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from cuentas.permisos import PermisoSistema, puede

from .modelos import AsignacionDimension, Carrera, Ciclo, Facultad
from .serializadores import (
    AsignacionDimensionCrearSerializador,
    AsignacionDimensionQuitarSerializador,
    AsignacionDimensionSerializador,
    CarreraSerializador,
    CicloCierreSerializador,
    CicloSerializador,
    FacultadSerializador,
)


def _validar_permiso(request, accion, *, entidad=None):
    usuario = getattr(request, "user", None)
    if usuario is None or not getattr(usuario, "is_authenticated", False):
        return
    if not puede(usuario, accion):
        raise PermisoSistema(
            "No tiene permiso para realizar esta acción.",
            accion=accion,
            entidad=entidad or "Recurso",
        )


class ListaCrearFacultadesVista(generics.ListCreateAPIView):
    permission_classes = (AllowAny,)
    queryset = Facultad.objects.order_by("nombre", "pk")
    serializer_class = FacultadSerializador

    def post(self, request, *args, **kwargs):
        _validar_permiso(request, "crear_facultad", entidad="Facultad")
        return super().post(request, *args, **kwargs)


class ListaCrearCarrerasVista(generics.ListCreateAPIView):
    permission_classes = (AllowAny,)
    queryset = Carrera.objects.select_related("facultad").order_by("nombre", "pk")
    serializer_class = CarreraSerializador

    def post(self, request, *args, **kwargs):
        _validar_permiso(request, "crear_carrera", entidad="Carrera")
        return super().post(request, *args, **kwargs)


class DetalleCarreraVista(generics.RetrieveUpdateAPIView):
    permission_classes = (AllowAny,)
    queryset = Carrera.objects.select_related("facultad").all()
    serializer_class = CarreraSerializador
    http_method_names = ["get", "patch", "head", "options"]


class ListaCrearCiclosVista(generics.ListCreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = CicloSerializador

    def post(self, request, *args, **kwargs):
        _validar_permiso(request, "abrir_ciclo", entidad="Ciclo")
        return super().post(request, *args, **kwargs)

    def get_queryset(self):
        queryset = Ciclo.objects.select_related(
            "carrera",
            "version_normativa",
            "ciclo_anterior",
        ).order_by("-anio_base", "-pk")
        carrera = self.request.query_params.get("carrera")
        if carrera:
            queryset = queryset.filter(carrera_id=carrera)
        estado = self.request.query_params.get("estado")
        if estado:
            queryset = queryset.filter(estado=estado)
        return queryset


class DetalleCicloVista(generics.RetrieveAPIView):
    permission_classes = (AllowAny,)
    queryset = Ciclo.objects.select_related(
        "carrera",
        "version_normativa",
        "ciclo_anterior",
    )
    serializer_class = CicloSerializador

    def get_object(self):
        ciclo = self.get_queryset().filter(pk=self.kwargs["pk"]).first()
        if ciclo is None:
            raise NotFound()
        return ciclo


class CerrarCicloVista(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, pk):
        _validar_permiso(request, "cerrar_ciclo", entidad="Ciclo")
        ciclo = get_object_or_404(Ciclo.objects.all(), pk=pk)
        serializer = CicloCierreSerializador(data=request.data, context={"ciclo": ciclo})
        serializer.is_valid(raise_exception=True)
        ciclo = serializer.save()
        return Response(CicloSerializador(ciclo).data, status=status.HTTP_200_OK)


class AsignacionesCicloVista(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = AsignacionDimensionSerializador

    def get_ciclo(self):
        return get_object_or_404(Ciclo.objects.all(), pk=self.kwargs["pk"])

    def get(self, request, pk):
        ciclo = self.get_ciclo()
        queryset = AsignacionDimension.objects.filter(ciclo=ciclo).select_related(
            "usuario",
            "dimension",
        ).order_by("pk")
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = AsignacionDimensionSerializador(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = AsignacionDimensionSerializador(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, pk):
        _validar_permiso(request, "asignar_dimension", entidad="AsignacionDimension")
        ciclo = self.get_ciclo()
        serializer = AsignacionDimensionCrearSerializador(
            data=request.data,
            context={"ciclo": ciclo},
        )
        serializer.is_valid(raise_exception=True)
        asignacion = serializer.save()
        respuesta = AsignacionDimensionSerializador(asignacion)
        return Response(respuesta.data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        _validar_permiso(request, "quitar_asignacion", entidad="AsignacionDimension")
        ciclo = self.get_ciclo()
        serializer = AsignacionDimensionQuitarSerializador(
            data=request.data,
            context={"ciclo": ciclo},
        )
        serializer.is_valid(raise_exception=True)
        eliminados = serializer.save()
        if eliminados == 0:
            raise NotFound("No existe la asignación indicada.")
        return Response(status=status.HTTP_204_NO_CONTENT)
