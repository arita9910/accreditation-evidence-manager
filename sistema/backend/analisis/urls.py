from django.urls import path

from . import vistas


urlpatterns = [
    path("ciclos/<int:pk>/estado/", vistas.EstadoCicloVista.as_view(), name="analisis-estado"),
    path(
        "ciclos/<int:pk>/completitud/",
        vistas.CompletitudCicloVista.as_view(),
        name="analisis-completitud",
    ),
    path(
        "comparaciones/",
        vistas.ComparacionCiclosVista.as_view(),
        name="analisis-comparacion",
    ),
]
