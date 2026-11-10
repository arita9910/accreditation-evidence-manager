import re
from datetime import datetime

from django.db.models import Q
from django.shortcuts import resolve_url
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from cuentas.permisos import puede

from .modelos import RegistroAuditoria
from .serializadores import RegistroAuditoriaSerializer


class PaginacionAuditoria(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


def _carreras_director(usuario):
    if usuario is None:
        return []
    valores = []
    for nombre in ("carrera_id", "carrera", "carrera_actual", "carrera_pk"):
        valor = getattr(usuario, nombre, None)
        if valor is not None:
            if hasattr(valor, "pk"):
                valores.append(valor.pk)
            else:
                valores.append(valor)
    for nombre in ("carreras", "carreras_asignadas", "carreras_director"):
        coleccion = getattr(usuario, nombre, None)
        if coleccion is None:
            continue
        if hasattr(coleccion, "all"):
            coleccion = coleccion.all()
        for item in coleccion:
            if hasattr(item, "pk"):
                valores.append(item.pk)
            elif isinstance(item, (int, str)):
                valores.append(item)
    ids = []
    for valor in valores:
        if isinstance(valor, str) and valor.isdigit():
            ids.append(int(valor))
        elif isinstance(valor, int):
            ids.append(valor)
    return list(dict.fromkeys(ids))


def _aplicar_contexto_sesion(request, usuario):
    if request is None or usuario is None:
        return usuario
    sesion = getattr(request, "session", None)
    if sesion is None:
        return usuario

    if not hasattr(usuario, "rol"):
        rol = sesion.get("rol") or sesion.get("role") or sesion.get("perfil")
        if rol is not None:
            setattr(usuario, "rol", rol)
    if not hasattr(usuario, "carrera_id"):
        carrera_id = sesion.get("carrera_id") or sesion.get("carrera")
        if carrera_id is not None:
            setattr(usuario, "carrera_id", carrera_id)
    return usuario


def _parsear_fecha_iso(valor):
    if valor is None:
        return None
    texto = str(valor).strip()
    if not texto:
        return None
    if texto.endswith("Z"):
        texto = texto[:-1] + "+00:00"
    if re.search(r"\s\d{2}:\d{2}$", texto):
        texto = re.sub(r"\s(\d{2}:\d{2})$", r"+\1", texto)
    try:
        return datetime.fromisoformat(texto)
    except ValueError:
        return None


def _aplicar_filtros(queryset, params):
    filtro = Q()
    usuario = params.get("usuario")
    if usuario:
        filtro &= Q(usuario__username__icontains=usuario) | Q(usuario__username__iexact=usuario)
    accion = params.get("accion")
    if accion:
        filtro &= Q(accion__icontains=accion)
    entidad = params.get("entidad")
    if entidad:
        filtro &= Q(entidad__icontains=entidad)
    resultado = params.get("resultado")
    if resultado:
        filtro &= Q(resultado=resultado)
    desde = params.get("desde") or params.get("fecha_desde") or params.get("fecha_inicio")
    if desde:
        fecha_desde = _parsear_fecha_iso(desde)
        if fecha_desde is None:
            raise PermissionDenied("La fecha de inicio no es válida.")
        filtro &= Q(fecha_hora__gte=fecha_desde)
    hasta = params.get("hasta") or params.get("fecha_hasta") or params.get("fecha_fin")
    if hasta:
        fecha_hasta = _parsear_fecha_iso(hasta)
        if fecha_hasta is None:
            raise PermissionDenied("La fecha de fin no es válida.")
        filtro &= Q(fecha_hora__lte=fecha_hasta)
    return queryset.filter(filtro)


def _acceso_registros(request):
    usuario = getattr(request, "user", None)
    if usuario is None or not getattr(usuario, "is_authenticated", False):
        raise PermissionDenied("No tiene permiso para consultar la auditoría.")
    usuario = _aplicar_contexto_sesion(request, usuario)
    if puede(usuario, "consultar_auditoria"):
        queryset = RegistroAuditoria.objects.select_related("usuario")
        if getattr(usuario, "rol", None) == "director_carrera" or getattr(usuario, "es_director", False) or getattr(usuario, "es_director_carrera", False):
            carreras = _carreras_director(usuario)
            if not carreras:
                return queryset.none()
            queryset = queryset.filter(
                Q(detalle__carrera_id__in=carreras) | Q(contexto__carrera_id__in=carreras)
            )
        return queryset
    raise PermissionDenied("No tiene permiso para consultar la auditoría.")


@api_view(["GET"])
@permission_classes([AllowAny])
def listar_auditoria(request):
    queryset = _acceso_registros(request)
    queryset = _aplicar_filtros(queryset, request.query_params)
    queryset = queryset.order_by("-fecha_hora", "-id")
    paginator = PaginacionAuditoria()
    page = paginator.paginate_queryset(queryset, request)
    serializer = RegistroAuditoriaSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)
