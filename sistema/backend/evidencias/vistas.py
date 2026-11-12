from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ciclos.modelos import Ciclo
from cuentas.permisos import PermisoSistema, puede
from estructura.models import Criterio, TipoEvidencia

from .busqueda import buscar
from .modelos import Clasificacion, Evidencia, FicheroEvidencia
from .serializadores import (
    ClasificacionCrearSerializador,
    ClasificacionSerializador,
    EvidenciaActualizarSerializador,
    EvidenciaCrearSerializador,
    EvidenciaSerializador,
    FicheroEvidenciaSerializador,
    FicheroSubidaSerializador,
    TipoEvidenciaOpcionSerializador,
)
from .servicios import descargar, quitar_clasificacion, verificar_huellas


def _validar_permiso(request, accion, *, entidad=None, objeto=None):
    usuario = getattr(request, "user", None)
    if usuario is None or not getattr(usuario, "is_authenticated", False):
        return
    if not puede(usuario, accion, objeto=objeto):
        raise PermisoSistema(
            "No tiene permiso para realizar esta acción.",
            accion=accion,
            entidad=entidad or "Recurso",
        )


class EvidenciaListaVista(generics.ListCreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = EvidenciaSerializador

    def get_queryset(self):
        params = self.request.query_params
        filtros = {
            "dimension": params.get("dimension") or params.get("dimension_id"),
            "indicador": params.get("indicador") or params.get("indicador_id"),
            "criterio": params.get("criterio") or params.get("criterio_id"),
            "curso": params.get("curso") or params.get("curso_academico"),
            "soporte": params.get("soporte"),
            "tipo": params.get("tipo") or params.get("tipo_evidencia") or params.get("tipo_evidencia_id"),
            "texto": params.get("q") or params.get("texto") or params.get("search"),
        }
        ciclo_id = params.get("ciclo")
        if ciclo_id:
            return buscar(ciclo_id, texto=filtros["texto"], filtros=filtros)
        return buscar(texto=filtros["texto"], filtros=filtros)

    def post(self, request, *args, **kwargs):
        _validar_permiso(request, "crear_evidencia", entidad="Evidencia", objeto=request.data)
        serializer = EvidenciaCrearSerializador(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        evidencia = serializer.save()
        return Response(EvidenciaSerializador(evidencia).data, status=status.HTTP_201_CREATED)


class TipoEvidenciaListaVista(generics.ListAPIView):
    permission_classes = (AllowAny,)
    serializer_class = TipoEvidenciaOpcionSerializador

    def get_queryset(self):
        queryset = TipoEvidencia.objects.select_related("dimension").order_by(
            "dimension__orden",
            "nombre",
        )
        ciclo_id = self.request.query_params.get("ciclo")
        if ciclo_id not in (None, ""):
            queryset = queryset.filter(dimension__version__ciclos__id=ciclo_id).distinct()
        return queryset


class EvidenciaDetalleVista(generics.RetrieveUpdateAPIView):
    permission_classes = (AllowAny,)
    queryset = Evidencia.objects.select_related(
        "ciclo__carrera",
        "tipo_evidencia__dimension",
    ).prefetch_related(
        "clasificaciones__criterio__indicador__dimension",
        "ficheros",
    )
    serializer_class = EvidenciaSerializador
    http_method_names = ["get", "patch", "head", "options"]

    def patch(self, request, *args, **kwargs):
        evidencia = self.get_object()
        _validar_permiso(request, "crear_evidencia", entidad="Evidencia", objeto=evidencia)
        serializer = EvidenciaActualizarSerializador(evidencia, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        evidencia = serializer.save()
        return Response(EvidenciaSerializador(evidencia).data)


class EvidenciaFicheroVista(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, pk):
        evidencia = get_object_or_404(Evidencia.objects.all(), pk=pk)
        _validar_permiso(request, "reemplazar_fichero", entidad="FicheroEvidencia", objeto=evidencia)
        serializer = FicheroSubidaSerializador(
            data=request.data,
            context={"request": request, "evidencia": evidencia},
        )
        serializer.is_valid(raise_exception=True)
        fichero = serializer.save()
        return Response(FicheroEvidenciaSerializador(fichero).data, status=status.HTTP_201_CREATED)


class EvidenciaFicheroActualVista(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, pk):
        evidencia = get_object_or_404(Evidencia.objects.all(), pk=pk)
        fichero = evidencia.ficheros.filter(vigente=True).order_by("-version").first()
        if fichero is None:
            raise get_object_or_404(FicheroEvidencia.objects.none(), pk=0)
        return descargar(fichero, usuario=request.user)


class FicheroDescargaVista(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, pk):
        fichero = get_object_or_404(FicheroEvidencia.objects.select_related("evidencia"), pk=pk)
        return descargar(fichero, usuario=request.user)


class EvidenciaClasificacionesVista(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, pk):
        evidencia = get_object_or_404(Evidencia.objects.all(), pk=pk)
        _validar_permiso(request, "crear_evidencia", entidad="Clasificacion", objeto=evidencia)
        serializer = ClasificacionCrearSerializador(
            data=request.data,
            context={"request": request, "evidencia": evidencia},
        )
        serializer.is_valid(raise_exception=True)
        clasificacion = serializer.save()
        return Response(ClasificacionSerializador(clasificacion).data, status=status.HTTP_201_CREATED)

    def delete(self, request, pk):
        evidencia = get_object_or_404(Evidencia.objects.all(), pk=pk)
        criterio_id = request.data.get("criterio") or request.data.get("criterio_id")
        if criterio_id is None:
            return Response({"detalle": "Debe indicar el criterio a quitar."}, status=status.HTTP_400_BAD_REQUEST)
        criterio = get_object_or_404(Criterio.objects.all(), pk=criterio_id)
        _validar_permiso(request, "crear_evidencia", entidad="Clasificacion", objeto=evidencia)
        quitar_clasificacion(evidencia, criterio, usuario=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CicloVerificacionHuellaVista(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, pk):
        ciclo = get_object_or_404(Ciclo.objects.all(), pk=pk)
        _validar_permiso(request, "verificar_huellas", entidad="Ciclo", objeto=ciclo)
        return Response(verificar_huellas(ciclo))

    def get(self, request, pk):
        return self.post(request, pk)


class EvidenciasPorCriterioVista(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, codigo):
        criterio = get_object_or_404(
            Criterio.objects.select_related("indicador__dimension__version").all(),
            codigo=codigo,
        )
        ciclo_id = request.query_params.get("ciclo")
        queryset = buscar(ciclo_id, filtros={"criterio": criterio.pk})
        serializer = EvidenciaSerializador(queryset, many=True)
        return Response(serializer.data)
