from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ciclos.modelos import Ciclo
from cuentas.permisos import puede

from .serializadores import (
    ComparacionSerializador,
    CompletitudSerializador,
    EstadoCicloSerializador,
)
from .servicios import comparar, completitud, estado_ciclo


def respuesta_error(codigo, mensaje, detalle=None, status_code=status.HTTP_400_BAD_REQUEST):
    return Response(
        {
            "codigo": codigo,
            "mensaje": mensaje,
            "detalle": detalle or {},
        },
        status=status_code,
    )


def usuario_autenticado(request):
    usuario = getattr(request, "user", None)
    if usuario is None or not getattr(usuario, "is_authenticated", False):
        return None
    return usuario


def puede_consultar(request, usuario, accion, ciclo):
    if not puede(usuario, accion, objeto=ciclo):
        return False
    if getattr(usuario, "rol", None) == "director_carrera":
        return getattr(usuario, "carrera_id", None) == ciclo.carrera_id
    return True


def denegar(request, accion, entidad):
    request.accion_denegada = accion
    request.entidad_denegada = entidad


class EstadoCicloVista(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, pk):
        usuario = usuario_autenticado(request)
        if usuario is None:
            denegar(request, "consultar_estado_analisis", "Ciclo")
            return respuesta_error(
                "autenticacion_requerida",
                "Se requiere autenticación.",
                {"sesion": "autenticación requerida"},
                status.HTTP_403_FORBIDDEN,
            )

        ciclo = Ciclo.objects.select_related("carrera", "version_normativa").filter(pk=pk).first()
        if ciclo is None:
            return respuesta_error(
                "ciclo_no_encontrado",
                "No existe el ciclo indicado.",
                {"ciclo_id": pk},
                status.HTTP_404_NOT_FOUND,
            )
        if not puede_consultar(request, usuario, "consultar_estado_analisis", ciclo):
            denegar(request, "consultar_estado_analisis", "Ciclo")
            return respuesta_error(
                "permiso_denegado",
                "No tiene permiso para consultar este ciclo.",
                {"ciclo_id": pk},
                status.HTTP_403_FORBIDDEN,
            )

        payload = estado_ciclo(ciclo, usuario=usuario).to_dict()
        serializer = EstadoCicloSerializador(payload)
        return Response(serializer.data)


class CompletitudCicloVista(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, pk):
        usuario = usuario_autenticado(request)
        if usuario is None:
            denegar(request, "consultar_completitud_analisis", "Ciclo")
            return respuesta_error(
                "autenticacion_requerida",
                "Se requiere autenticación.",
                {"sesion": "autenticación requerida"},
                status.HTTP_403_FORBIDDEN,
            )

        ciclo = Ciclo.objects.select_related("carrera", "version_normativa").filter(pk=pk).first()
        if ciclo is None:
            return respuesta_error(
                "ciclo_no_encontrado",
                "No existe el ciclo indicado.",
                {"ciclo_id": pk},
                status.HTTP_404_NOT_FOUND,
            )
        if not puede_consultar(request, usuario, "consultar_completitud_analisis", ciclo):
            denegar(request, "consultar_completitud_analisis", "Ciclo")
            return respuesta_error(
                "permiso_denegado",
                "No tiene permiso para consultar este ciclo.",
                {"ciclo_id": pk},
                status.HTTP_403_FORBIDDEN,
            )

        payload = completitud(ciclo, usuario=usuario).to_dict()
        serializer = CompletitudSerializador(payload)
        return Response(serializer.data)


class ComparacionCiclosVista(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        usuario = usuario_autenticado(request)
        if usuario is None:
            denegar(request, "comparar_ciclos", "Ciclo")
            return respuesta_error(
                "autenticacion_requerida",
                "Se requiere autenticación.",
                {"sesion": "autenticación requerida"},
                status.HTTP_403_FORBIDDEN,
            )

        a = request.query_params.get("a")
        b = request.query_params.get("b")
        if not a or not b:
            return respuesta_error(
                "parametros_invalidos",
                "Debe indicar los ciclos a y b.",
                {"a": a, "b": b},
                status.HTTP_400_BAD_REQUEST,
            )
        try:
            ciclo_a_id = int(a)
            ciclo_b_id = int(b)
        except (TypeError, ValueError):
            return respuesta_error(
                "parametros_invalidos",
                "Los identificadores de ciclo deben ser números.",
                {"a": a, "b": b},
                status.HTTP_400_BAD_REQUEST,
            )

        ciclo_a = (
            Ciclo.objects.select_related("carrera", "version_normativa")
            .filter(pk=ciclo_a_id)
            .first()
        )
        ciclo_b = (
            Ciclo.objects.select_related("carrera", "version_normativa")
            .filter(pk=ciclo_b_id)
            .first()
        )
        if ciclo_a is None or ciclo_b is None:
            return respuesta_error(
                "ciclo_no_encontrado",
                "No existe el ciclo indicado.",
                {"a": ciclo_a_id, "b": ciclo_b_id},
                status.HTTP_404_NOT_FOUND,
            )
        if ciclo_a.carrera_id != ciclo_b.carrera_id:
            return respuesta_error(
                "carreras_distintas",
                "Los ciclos deben pertenecer a la misma carrera.",
                {"carrera_a": ciclo_a.carrera_id, "carrera_b": ciclo_b.carrera_id},
                status.HTTP_400_BAD_REQUEST,
            )
        if ciclo_a_id == ciclo_b_id:
            return respuesta_error(
                "comparacion_invalida",
                "Debe comparar dos ciclos distintos.",
                {"a": ciclo_a_id, "b": ciclo_b_id},
                status.HTTP_400_BAD_REQUEST,
            )
        if not puede(usuario, "comparar_ciclos", objeto=ciclo_a) or not puede(
            usuario, "comparar_ciclos", objeto=ciclo_b
        ):
            denegar(request, "comparar_ciclos", "Ciclo")
            return respuesta_error(
                "permiso_denegado",
                "No tiene permiso para realizar esta acción.",
                {"carrera_id": ciclo_a.carrera_id},
                status.HTTP_403_FORBIDDEN,
            )

        if getattr(usuario, "rol", None) == "director_carrera":
            if getattr(usuario, "carrera_id", None) not in (
                ciclo_a.carrera_id,
                ciclo_b.carrera_id,
            ):
                denegar(request, "comparar_ciclos", "Ciclo")
                return respuesta_error(
                    "permiso_denegado",
                    "No tiene permiso para realizar esta acción.",
                    {"carrera_id": ciclo_a.carrera_id},
                    status.HTTP_403_FORBIDDEN,
                )

        try:
            payload = comparar(ciclo_a, ciclo_b, usuario=usuario).to_dict()
        except DjangoValidationError as exc:
            return respuesta_error(
                "parametros_invalidos",
                "No se pudo realizar la comparación.",
                exc.message_dict if hasattr(exc, "message_dict") else {"errores": exc.messages},
                status.HTTP_400_BAD_REQUEST,
            )

        serializer = ComparacionSerializador(payload)
        return Response(serializer.data)
