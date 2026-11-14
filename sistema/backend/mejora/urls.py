from django.urls import path

from . import vistas

app_name = "mejora"

urlpatterns = [
    path("ciclos/<int:pk>/plan/", vistas.CicloPlanVista.as_view(), name="ciclo-plan"),
    path("planes/<int:pk>/acciones/", vistas.PlanAccionesVista.as_view(), name="plan-acciones"),
    path("acciones/<int:pk>/", vistas.AccionDetalleVista.as_view(), name="accion-detalle"),
    path("acciones/<int:pk>/estado/", vistas.AccionEstadoVista.as_view(), name="accion-estado"),
    path("acciones/<int:pk>/seguimientos/", vistas.SeguimientoAccionVista.as_view(), name="accion-seguimientos"),
    path("acciones/<int:pk>/evidencias/", vistas.AccionEvidenciaVista.as_view(), name="accion-evidencias"),
    path("ciclos/<int:pk>/plan-anterior/", vistas.CicloPlanAnteriorVista.as_view(), name="plan-anterior"),
]
