from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ciclos.modelos import Ciclo
from cuentas.permisos import PermisoSistema, puede

from .models import AccionEvidencia, AccionMejora, PlanMejora, SeguimientoAccion
from .serializers import (
    AccionEvidenciaCrearSerializer,
    AccionEvidenciaSerializer,
    AccionMejoraActualizarSerializer,
    AccionMejoraCrearSerializer,
    AccionMejoraSerializer,
    PlanMejoraActualizarSerializer,
    PlanMejoraCrearSerializer,
    PlanMejoraSerializer,
    SeguimientoAccionCrearSerializer,
    SeguimientoAccionSerializer,
)
from .servicios import eliminar_accion_mejora, plan_ciclo_anterior


def _puede_operar(request, accion, *, objeto=None):
    usuario = getattr(request, "user", None)
    if usuario is None or not getattr(usuario, "is_authenticated", False):
        return False
    return puede(usuario, accion, objeto=objeto)


def _validar_permiso(request, accion, *, entidad=None, objeto=None):
    if not _puede_operar(request, accion, objeto=objeto):
        raise PermisoSistema(
            "No tiene permiso para realizar esta acción.",
            accion=accion,
            entidad=entidad or "Recurso",
        )


class CicloPlanVista(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = PlanMejoraSerializer

    def get(self, request, pk):
        ciclo = get_object_or_404(Ciclo.objects.all(), pk=pk)
        if not _puede_operar(request, "crear_plan_mejora", objeto=ciclo):
            raise PermisoSistema("No tiene permiso para consultar este plan.", accion="crear_plan_mejora", entidad="PlanMejora")
        plan = get_object_or_404(PlanMejora.objects.select_related("ciclo", "aprobado_por"), ciclo=ciclo)
        return Response(PlanMejoraSerializer(plan).data)

    def post(self, request, pk):
        ciclo = get_object_or_404(Ciclo.objects.all(), pk=pk)
        _validar_permiso(request, "crear_plan_mejora", entidad="PlanMejora", objeto=ciclo)
        serializer = PlanMejoraCrearSerializer(
            data=request.data,
            context={"request": request, "ciclo": ciclo, "usuario": request.user},
        )
        serializer.is_valid(raise_exception=True)
        plan = serializer.save()
        return Response(PlanMejoraSerializer(plan).data, status=status.HTTP_201_CREATED)


class PlanDetalleVista(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = PlanMejoraSerializer

    def get_object(self):
        return get_object_or_404(PlanMejora.objects.select_related("ciclo", "aprobado_por"), pk=self.kwargs["pk"])

    def patch(self, request, *args, **kwargs):
        plan = self.get_object()
        _validar_permiso(request, "crear_plan_mejora", entidad="PlanMejora", objeto=plan.ciclo)
        serializer = PlanMejoraActualizarSerializer(
            data=request.data,
            context={"request": request, "plan": plan, "usuario": request.user},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        plan = serializer.save()
        return Response(PlanMejoraSerializer(plan).data)


class PlanAccionesVista(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = AccionMejoraSerializer

    def get_plan(self):
        return get_object_or_404(PlanMejora.objects.select_related("ciclo"), pk=self.kwargs["pk"])

    def get(self, request, *args, **kwargs):
        plan = self.get_plan()
        if not _puede_operar(request, "proponer_accion", objeto=plan.ciclo):
            raise PermisoSistema("No tiene permiso para consultar estas acciones.", accion="proponer_accion", entidad="AccionMejora")
        queryset = AccionMejora.objects.filter(plan=plan).select_related("plan", "debilidad", "responsable").order_by("pk")
        return Response(AccionMejoraSerializer(queryset, many=True).data)

    def post(self, request, *args, **kwargs):
        plan = self.get_plan()
        _validar_permiso(request, "proponer_accion", entidad="AccionMejora", objeto=plan.ciclo)
        serializer = AccionMejoraCrearSerializer(
            data=request.data,
            context={"request": request, "plan": plan, "usuario": request.user},
        )
        serializer.is_valid(raise_exception=True)
        accion = serializer.save()
        return Response(AccionMejoraSerializer(accion).data, status=status.HTTP_201_CREATED)


class AccionDetalleVista(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = AccionMejoraSerializer

    def get_object(self):
        return get_object_or_404(
            AccionMejora.objects.select_related("plan__ciclo", "debilidad", "responsable"),
            pk=self.kwargs["pk"],
        )

    def patch(self, request, *args, **kwargs):
        accion = self.get_object()
        if "estado" in request.data:
            _validar_permiso(request, "aprobar_accion", entidad="AccionMejora", objeto=accion.plan.ciclo)
        else:
            _validar_permiso(request, "proponer_accion", entidad="AccionMejora", objeto=accion.plan.ciclo)

        serializer = AccionMejoraActualizarSerializer(
            data=request.data,
            context={"request": request, "accion": accion, "usuario": request.user},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        accion = serializer.save()
        return Response(AccionMejoraSerializer(accion).data)

    def put(self, request, *args, **kwargs):
        return self.patch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        accion = self.get_object()
        if not _puede_operar(request, "proponer_accion", objeto=accion.plan.ciclo):
            raise PermisoSistema("No tiene permiso para consultar esta acción.", accion="proponer_accion", entidad="AccionMejora")
        return Response(AccionMejoraSerializer(accion).data)

    def delete(self, request, *args, **kwargs):
        accion = self.get_object()
        _validar_permiso(request, "proponer_accion", entidad="AccionMejora", objeto=accion.plan.ciclo)
        eliminar_accion_mejora(accion, usuario=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AccionEstadoVista(generics.GenericAPIView):
    permission_classes = (AllowAny,)

    def get_object(self):
        return get_object_or_404(AccionMejora.objects.select_related("plan__ciclo"), pk=self.kwargs["pk"])

    def post(self, request, *args, **kwargs):
        accion = self.get_object()
        _validar_permiso(request, "aprobar_accion", entidad="AccionMejora", objeto=accion.plan.ciclo)
        estado = request.data.get("estado")
        nota = request.data.get("nota")
        if estado is None or str(estado).strip() == "":
            return Response({"detalle": "Debe indicar un estado válido."}, status=status.HTTP_400_BAD_REQUEST)
        serializer = AccionMejoraActualizarSerializer(
            data={"estado": estado, "nota": nota or ""},
            context={"request": request, "accion": accion, "usuario": request.user},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        accion = serializer.save()
        return Response(AccionMejoraSerializer(accion).data)


class SeguimientoAccionVista(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = SeguimientoAccionSerializer

    def get_object(self):
        return get_object_or_404(AccionMejora.objects.select_related("plan__ciclo"), pk=self.kwargs["pk"])

    def get(self, request, *args, **kwargs):
        accion = self.get_object()
        if not _puede_operar(request, "registrar_seguimiento", objeto=accion.plan.ciclo):
            raise PermisoSistema("No tiene permiso para consultar este historial.", accion="registrar_seguimiento", entidad="SeguimientoAccion")
        queryset = SeguimientoAccion.objects.filter(accion=accion).select_related("accion", "registrado_por").order_by("-fecha")
        return Response(SeguimientoAccionSerializer(queryset, many=True).data)

    def post(self, request, *args, **kwargs):
        accion = self.get_object()
        _validar_permiso(request, "registrar_seguimiento", entidad="SeguimientoAccion", objeto=accion.plan.ciclo)
        serializer = SeguimientoAccionCrearSerializer(
            data=request.data,
            context={"request": request, "accion": accion, "usuario": request.user},
        )
        serializer.is_valid(raise_exception=True)
        seguimiento = serializer.save()
        return Response(SeguimientoAccionSerializer(seguimiento).data, status=status.HTTP_201_CREATED)


class AccionEvidenciaVista(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = AccionEvidenciaSerializer

    def get_object(self):
        return get_object_or_404(AccionMejora.objects.select_related("plan__ciclo"), pk=self.kwargs["pk"])

    def post(self, request, *args, **kwargs):
        accion = self.get_object()
        _validar_permiso(request, "vincular_evidencia", entidad="AccionEvidencia", objeto=accion.plan.ciclo)
        serializer = AccionEvidenciaCrearSerializer(
            data=request.data,
            context={"request": request, "accion": accion, "usuario": request.user},
        )
        serializer.is_valid(raise_exception=True)
        evidencia = serializer.save()
        return Response(AccionEvidenciaSerializer(evidencia).data, status=status.HTTP_201_CREATED)


class CicloPlanAnteriorVista(generics.GenericAPIView):
    permission_classes = (AllowAny,)

    def get(self, request, pk):
        ciclo = get_object_or_404(Ciclo.objects.select_related("ciclo_anterior"), pk=pk)
        if not _puede_operar(request, "crear_plan_mejora", objeto=ciclo):
            raise PermisoSistema("No tiene permiso para consultar el plan anterior.", accion="crear_plan_mejora", entidad="PlanMejora")
        plan = plan_ciclo_anterior(ciclo)
        if plan is None:
            return Response({"detalle": "No existe un plan anterior para este ciclo."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "plan": PlanMejoraSerializer(plan).data,
                "acciones": AccionMejoraSerializer(plan.acciones.select_related("plan", "debilidad", "responsable").order_by("pk"), many=True).data,
            }
        )


__all__ = [
    "CicloPlanVista",
    "PlanDetalleVista",
    "PlanAccionesVista",
    "AccionDetalleVista",
    "AccionEstadoVista",
    "SeguimientoAccionVista",
    "AccionEvidenciaVista",
    "CicloPlanAnteriorVista",
]
