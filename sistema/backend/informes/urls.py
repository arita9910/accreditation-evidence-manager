from django.urls import path

from . import vistas


urlpatterns = [
    path(
        "ciclos/<int:pk>/informe/generar/",
        vistas.GenerarInformeVista.as_view(),
        name="generar-informe",
    ),
    path(
        "ciclos/<int:pk>/informe/textos/",
        vistas.TextosInformeListaVista.as_view(),
        name="textos-informe",
    ),
    path(
        "ciclos/<int:pk>/informe/textos/<str:seccion>/",
        vistas.TextoInformeSeccionVista.as_view(),
        name="texto-informe-seccion",
    ),
    path(
        "ciclos/<int:pk>/informe/versiones/",
        vistas.VersionesInformeListaVista.as_view(),
        name="versiones-informe",
    ),
    path(
        "informes/versiones/<int:pk>/descarga/",
        vistas.DescargarVersionInformeVista.as_view(),
        name="descargar-version-informe",
    ),
    path(
        "ciclos/<int:pk>/expediente/",
        vistas.ExpedienteCicloVista.as_view(),
        name="expediente-ciclo",
    ),
    path(
        "ciclos/<int:pk>/expediente/ficheros/<int:fichero_id>/descarga/",
        vistas.DescargarFicheroExpedienteVista.as_view(),
        name="descargar-fichero-expediente",
    ),
]
