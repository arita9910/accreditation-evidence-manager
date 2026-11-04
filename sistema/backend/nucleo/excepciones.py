from rest_framework.exceptions import (
    AuthenticationFailed,
    MethodNotAllowed,
    NotAuthenticated,
    NotFound,
    PermissionDenied,
    Throttled,
    ValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler


_MENSAJES = {
    "invalid": "La solicitud contiene datos no válidos.",
    "not_authenticated": "Se requiere autenticación.",
    "authentication_failed": "Las credenciales no son válidas.",
    "permission_denied": "No tiene permiso para realizar esta acción.",
    "not_found": "El recurso solicitado no existe.",
    "method_not_allowed": "El método HTTP no está permitido.",
    "throttled": "Se han recibido demasiadas solicitudes.",
}


def manejador_excepciones(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    codigo = getattr(exc, "default_code", "error")
    mensaje = _MENSAJES.get(codigo, "No se pudo completar la solicitud.")
    if isinstance(exc, ValidationError):
        mensaje = _MENSAJES["invalid"]
    elif isinstance(exc, NotAuthenticated):
        mensaje = _MENSAJES["not_authenticated"]
    elif isinstance(exc, AuthenticationFailed):
        mensaje = _MENSAJES["authentication_failed"]
    elif isinstance(exc, PermissionDenied):
        mensaje = _MENSAJES["permission_denied"]
    elif isinstance(exc, NotFound):
        mensaje = _MENSAJES["not_found"]
    elif isinstance(exc, MethodNotAllowed):
        mensaje = _MENSAJES["method_not_allowed"]
    elif isinstance(exc, Throttled):
        mensaje = _MENSAJES["throttled"]

    response.data = {
        "codigo": codigo,
        "mensaje": mensaje,
        "detalle": response.data,
    }
    return response
