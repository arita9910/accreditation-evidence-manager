from django.urls import path

from . import vistas

urlpatterns = [
    path(
        "ciclos/<int:pk>/valoraciones/catalogo/",
        vistas.ValoracionesCatalogoCicloVista.as_view(),
        name="valoraciones-ciclo-catalogo",
    ),
    path("ciclos/<int:pk>/valoraciones/", vistas.ValoracionesCicloVista.as_view(), name="valoraciones-ciclo"),
    path("valoraciones/<int:pk>/", vistas.ValoracionDetalleVista.as_view(), name="valoracion-detalle"),
]
