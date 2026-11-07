from django.urls import path

from . import vistas


urlpatterns = [
    path("facultades/", vistas.ListaCrearFacultadesVista.as_view(), name="facultades"),
    path("carreras/", vistas.ListaCrearCarrerasVista.as_view(), name="carreras"),
    path("carreras/<int:pk>/", vistas.DetalleCarreraVista.as_view(), name="carrera"),
    path("ciclos/", vistas.ListaCrearCiclosVista.as_view(), name="ciclos"),
    path("ciclos/<int:pk>/", vistas.DetalleCicloVista.as_view(), name="ciclo"),
    path("ciclos/<int:pk>/cerrar/", vistas.CerrarCicloVista.as_view(), name="cerrar-ciclo"),
    path(
        "ciclos/<int:pk>/asignaciones/",
        vistas.AsignacionesCicloVista.as_view(),
        name="asignaciones-ciclo",
    ),
]
