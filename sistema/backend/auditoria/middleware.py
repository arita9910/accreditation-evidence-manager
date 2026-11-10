from rest_framework.exceptions import PermissionDenied

from auditoria.servicios import registrar


class AuditoriaAccesoDenegadoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
        except PermissionDenied:
            self._registrar_acceso_denegado(request)
            raise

        if response.status_code == 403:
            self._registrar_acceso_denegado(request)
        return response

    def _registrar_acceso_denegado(self, request):
        usuario = getattr(request, "user", None)
        if usuario is None or not getattr(usuario, "is_authenticated", False):
            return

        entidad = getattr(request, "entidad_denegada", None)
        if entidad is None:
            match = getattr(request, "resolver_match", None)
            if match is not None:
                entidad = match.url_name or match.route or "Recurso"
            else:
                entidad = request.path.rstrip("/").split("/")[-1] or "Recurso"

        accion = getattr(request, "accion_denegada", None) or "acceso.denegado"
        detalle = {
            "method": request.method,
            "path": request.path,
            "query": self._filtrar_datos(request.GET),
            "accion": accion,
        }
        registrar(
            "acceso.denegado",
            usuario=usuario,
            entidad=entidad,
            detalle=detalle,
            contexto={"path": request.path, "method": request.method, "accion": accion, "entidad": entidad},
            resultado="denegado",
            ip=request.META.get("REMOTE_ADDR"),
        )

    @staticmethod
    def _filtrar_datos(datos):
        if not datos:
            return {}
        filtrados = {}
        for clave, valor in datos.lists():
            key_lower = clave.lower()
            if any(token in key_lower for token in ("password", "token", "secret", "authorization", "cookie")):
                filtrados[clave] = "[filtrado]"
            else:
                filtrados[clave] = valor[-1] if isinstance(valor, list) and valor else valor
        return filtrados
