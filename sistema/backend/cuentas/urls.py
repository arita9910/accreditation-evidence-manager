from django.urls import path

from . import vistas

urlpatterns = [
    path("sesion/", vistas.SesionVista.as_view(), name="sesion"),
    path("cuentas/cambiar-clave/", vistas.CambiarClaveVista.as_view(), name="cambiar-clave"),
    path("cuentas/yo/", vistas.PerfilAutenticadoVista.as_view(), name="mi-perfil"),
    path("usuarios/", vistas.ListaUsuariosVista.as_view(), name="usuarios"),
    path("usuarios/<int:pk>/", vistas.DetalleUsuarioVista.as_view(), name="usuario-detalle"),
    path("usuarios/<int:pk>/roles/", vistas.GestionRolesUsuarioVista.as_view(), name="usuario-roles"),
]
