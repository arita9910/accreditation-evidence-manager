import os
from datetime import datetime, timedelta

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.password_validation import validate_password
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from auditoria.servicios import registrar
from ciclos.modelos import Carrera

from .modelos import Usuario
from .permisos import puede
from .serializadores import UsuarioPerfilSerializer, UsuarioSerializer

MAX_INTENTOS_FALLIDOS = int(os.getenv("CUENTAS_MAX_INTENTOS_FALLIDOS", "5"))
BLOQUEO_SEGUNDOS = int(os.getenv("CUENTAS_BLOQUEO_SEGUNDOS", "300"))


class PermisoAdministradorTecnico(BasePermission):
    message = "Solo el administrador técnico puede gestionar usuarios y roles."

    def has_permission(self, request, view):
        usuario = getattr(request, "user", None)
        if usuario is None or not getattr(usuario, "is_authenticated", False):
            return False
        return bool(puede(usuario, "gestionar_usuarios"))


def _perfil_usuario(usuario):
    return UsuarioPerfilSerializer(usuario).data


def _bloqueado(request):
    sesion = getattr(request, "session", None)
    if sesion is None:
        return False
    bloqueado_hasta = sesion.get("login_bloqueado_hasta")
    if not bloqueado_hasta:
        return False
    try:
        return datetime.fromisoformat(bloqueado_hasta) > datetime.now()
    except (TypeError, ValueError):
        return False


def _registrar_intento_fallido(request, username):
    sesion = request.session
    sesion.setdefault("login_intentos_fallidos", 0)
    sesion["login_intentos_fallidos"] = int(sesion.get("login_intentos_fallidos", 0)) + 1
    if sesion["login_intentos_fallidos"] >= MAX_INTENTOS_FALLIDOS:
        sesion["login_bloqueado_hasta"] = (datetime.now() + timedelta(seconds=BLOQUEO_SEGUNDOS)).isoformat()
    sesion.modified = True
    registrar(
        "sesion.login_fallido",
        usuario=None,
        entidad="Usuario",
        detalle={"username": username, "intentos": sesion["login_intentos_fallidos"]},
        contexto={"username": username, "path": request.path, "method": request.method},
        resultado="denegado",
        ip=request.META.get("REMOTE_ADDR"),
    )


def _resetear_intentos_login(request):
    sesion = request.session
    sesion["login_intentos_fallidos"] = 0
    sesion.pop("login_bloqueado_hasta", None)
    sesion.modified = True


@method_decorator(csrf_protect, name="dispatch")
class SesionVista(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        username = (request.data.get("username") or "").strip()
        password = request.data.get("password") or ""

        if not username or not password:
            raise ValidationError({"detail": "El usuario y la contraseña son obligatorios."})

        if _bloqueado(request):
            registrar(
                "sesion.login_bloqueado",
                usuario=None,
                entidad="Usuario",
                detalle={"username": username},
                contexto={"username": username, "path": request.path, "method": request.method},
                resultado="denegado",
                ip=request.META.get("REMOTE_ADDR"),
            )
            raise PermissionDenied("Se ha excedido el número máximo de intentos. Inténtelo más tarde.")

        usuario = authenticate(request, username=username, password=password)
        if usuario is None:
            _registrar_intento_fallido(request, username)
            raise PermissionDenied("Las credenciales no son válidas.")

        if not getattr(usuario, "is_active", True):
            _registrar_intento_fallido(request, username)
            raise PermissionDenied("El usuario no está activo.")

        login(request, usuario)
        _resetear_intentos_login(request)
        registrar(
            "sesion.login",
            usuario=usuario,
            entidad="Usuario",
            detalle={"username": usuario.username},
            contexto={"username": usuario.username, "method": request.method},
            resultado="correcto",
            ip=request.META.get("REMOTE_ADDR"),
        )
        return Response({"mensaje": "Sesión iniciada.", "usuario": _perfil_usuario(usuario)}, status=status.HTTP_200_OK)

    def delete(self, request):
        usuario = getattr(request, "user", None)
        if usuario is not None and getattr(usuario, "is_authenticated", False):
            logout(request)
        registrar(
            "sesion.logout",
            usuario=usuario,
            entidad="Usuario",
            detalle={"logout": True},
            contexto={"path": request.path, "method": request.method},
            resultado="correcto",
            ip=request.META.get("REMOTE_ADDR"),
        )
        return Response({"mensaje": "Sesión cerrada."}, status=status.HTTP_200_OK)


@method_decorator(csrf_protect, name="dispatch")
class CambiarClaveVista(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        usuario = getattr(request, "user", None)
        if usuario is None or not getattr(usuario, "is_authenticated", False):
            raise PermissionDenied("Debe iniciar sesión para cambiar la contraseña.")

        password_actual = request.data.get("password_actual") or request.data.get("current_password")
        password_nueva = request.data.get("password_nueva") or request.data.get("new_password")
        if not password_actual or not password_nueva:
            raise ValidationError({"detail": "La contraseña actual y la nueva son obligatorias."})
        if not usuario.check_password(password_actual):
            registrar(
                "cuenta.cambiar_clave.denegado",
                usuario=usuario,
                entidad="Usuario",
                detalle={"username": usuario.username},
                contexto={"username": usuario.username, "path": request.path, "method": request.method},
                resultado="denegado",
                ip=request.META.get("REMOTE_ADDR"),
            )
            raise PermissionDenied("La contraseña actual no es válida.")

        try:
            validate_password(password_nueva, usuario)
        except Exception as exc:
            raise ValidationError({"password_nueva": [str(exc)]}) from exc

        usuario.set_password(password_nueva)
        usuario.save(update_fields=["password"])
        registrar(
            "cuenta.cambiar_clave",
            usuario=usuario,
            entidad="Usuario",
            detalle={"username": usuario.username},
            contexto={"username": usuario.username, "path": request.path, "method": request.method},
            resultado="correcto",
            ip=request.META.get("REMOTE_ADDR"),
        )
        return Response({"mensaje": "Contraseña actualizada."}, status=status.HTTP_200_OK)


@method_decorator(csrf_protect, name="dispatch")
class PerfilAutenticadoVista(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        usuario = getattr(request, "user", None)
        if usuario is None or not getattr(usuario, "is_authenticated", False):
            raise PermissionDenied("Debe iniciar sesión para consultar el perfil.")
        return Response(_perfil_usuario(usuario), status=status.HTTP_200_OK)


@method_decorator(csrf_protect, name="dispatch")
class ListaUsuariosVista(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        if not PermisoAdministradorTecnico().has_permission(request, self):
            request.accion_denegada = "listar_usuarios"
            request.entidad_denegada = "Usuario"
            raise PermissionDenied("No tiene permiso para listar usuarios.")
        queryset = Usuario.objects.select_related("carrera").order_by("username")
        serializer = UsuarioSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if not PermisoAdministradorTecnico().has_permission(request, self):
            request.accion_denegada = "crear_usuario"
            request.entidad_denegada = "Usuario"
            raise PermissionDenied("No tiene permiso para crear usuarios.")
        serializer = UsuarioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()
        registrar(
            "usuario.creado",
            usuario=request.user,
            entidad="Usuario",
            detalle={"username": usuario.username, "rol": usuario.rol},
            contexto={"usuario_id": usuario.pk, "rol": usuario.rol},
            resultado="correcto",
            ip=request.META.get("REMOTE_ADDR"),
        )
        return Response(UsuarioSerializer(usuario).data, status=status.HTTP_201_CREATED)


@method_decorator(csrf_protect, name="dispatch")
class DetalleUsuarioVista(APIView):
    permission_classes = (AllowAny,)

    def patch(self, request, pk):
        if not PermisoAdministradorTecnico().has_permission(request, self):
            request.accion_denegada = "editar_usuario"
            request.entidad_denegada = "Usuario"
            raise PermissionDenied("No tiene permiso para editar usuarios.")
        usuario = get_object_or_404(Usuario.objects.all(), pk=pk)
        serializer = UsuarioSerializer(usuario, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        usuario_actualizado = serializer.save()
        return Response(UsuarioSerializer(usuario_actualizado).data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        if not PermisoAdministradorTecnico().has_permission(request, self):
            request.accion_denegada = "eliminar_usuario"
            request.entidad_denegada = "Usuario"
            raise PermissionDenied("No tiene permiso para eliminar usuarios.")
        usuario = get_object_or_404(Usuario.objects.all(), pk=pk)
        if usuario == request.user:
            raise PermissionDenied("No puede eliminarse a sí mismo.")
        username = usuario.username
        usuario.delete()
        registrar(
            "usuario.eliminado",
            usuario=request.user,
            entidad="Usuario",
            detalle={"username": username},
            contexto={"usuario_id": pk},
            resultado="correcto",
            ip=request.META.get("REMOTE_ADDR"),
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


@method_decorator(csrf_protect, name="dispatch")
class GestionRolesUsuarioVista(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, pk):
        if not PermisoAdministradorTecnico().has_permission(request, self):
            request.accion_denegada = "listar_roles"
            request.entidad_denegada = "Usuario"
            raise PermissionDenied("No tiene permiso para gestionar roles.")
        usuario = get_object_or_404(Usuario.objects.select_related("carrera"), pk=pk)
        return Response(
            {
                "usuario_id": usuario.pk,
                "username": usuario.username,
                "rol": usuario.rol,
                "carrera": usuario.carrera_id,
                "carrera_nombre": usuario.carrera.nombre if usuario.carrera else None,
            },
            status=status.HTTP_200_OK,
        )

    def post(self, request, pk):
        if not PermisoAdministradorTecnico().has_permission(request, self):
            request.accion_denegada = "asignar_rol"
            request.entidad_denegada = "Usuario"
            raise PermissionDenied("No tiene permiso para asignar roles.")
        usuario = get_object_or_404(Usuario.objects.select_related("carrera"), pk=pk)
        rol = (request.data.get("rol") or request.data.get("role") or usuario.rol)
        if not isinstance(rol, str):
            raise ValidationError({"rol": "El rol indicado no es válido."})
        rol = rol.strip()
        carrera_id = request.data.get("carrera") or request.data.get("carrera_id")
        if rol not in dict(Usuario.Rol.choices):
            raise ValidationError({"rol": "El rol indicado no es válido."})
        if rol == Usuario.Rol.DIRECTOR_CARRERA:
            if carrera_id is None:
                raise ValidationError({"carrera": "Un director de carrera debe tener una carrera asociada."})
            carrera = get_object_or_404(Carrera.objects.all(), pk=carrera_id)
            usuario.carrera = carrera
        else:
            usuario.carrera = None
        usuario.rol = rol
        usuario.full_clean()
        usuario.save()
        registrar(
            "usuario.rol_actualizado",
            usuario=request.user,
            entidad="Usuario",
            detalle={"usuario_id": usuario.pk, "rol": usuario.rol, "carrera": usuario.carrera_id},
            contexto={"usuario_id": usuario.pk, "rol": usuario.rol, "carrera": usuario.carrera_id},
            resultado="correcto",
            ip=request.META.get("REMOTE_ADDR"),
        )
        return Response({"usuario_id": usuario.pk, "rol": usuario.rol, "carrera": usuario.carrera_id}, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        return self.post(request, pk)

    def delete(self, request, pk):
        if not PermisoAdministradorTecnico().has_permission(request, self):
            request.accion_denegada = "revocar_rol"
            request.entidad_denegada = "Usuario"
            raise PermissionDenied("No tiene permiso para revocar roles.")
        usuario = get_object_or_404(Usuario.objects.select_related("carrera"), pk=pk)
        if usuario == request.user:
            raise PermissionDenied("No se puede quitar el rol al usuario autenticado.")
        usuario.rol = Usuario.Rol.ADMINISTRADOR_TECNICO
        usuario.carrera = None
        usuario.full_clean()
        usuario.save()
        return Response({"usuario_id": usuario.pk, "rol": usuario.rol, "carrera": usuario.carrera_id}, status=status.HTTP_200_OK)