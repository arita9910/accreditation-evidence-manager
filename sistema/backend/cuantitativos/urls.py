from django.urls import path

from . import vistas

urlpatterns = [
    path(
        "ciclos/<int:pk>/modelos/<int:modelo_num>/valores/",
        vistas.CicloValoresModeloVista.as_view(),
        name="valores-modelo-por-ciclo",
    ),
    path(
        "ciclos/<int:pk>/criterios/<str:codigo>/valor/",
        vistas.CicloValorCriterioVista.as_view(),
        name="valor-criterio-por-ciclo",
    ),
    path("vinculos/", vistas.VinculoDatoVista.as_view(), name="vinculos-dato"),
    path("evidencias/<int:pk>/datos/", vistas.DatosEvidenciaVista.as_view(), name="datos-evidencia"),
    path("datos/<str:tipo>/<int:pk>/evidencias/", vistas.EvidenciasDatoVista.as_view(), name="evidencias-por-dato"),
    path(
        "ciclos/<int:pk>/datos/sin-respaldo/",
        vistas.DatosSinRespaldoCicloVista.as_view(),
        name="datos-sin-respaldo-ciclo",
    ),
]
