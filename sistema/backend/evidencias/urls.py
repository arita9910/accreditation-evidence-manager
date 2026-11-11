from django.urls import path

from . import vistas

urlpatterns = [
    path("evidencias/", vistas.EvidenciaListaVista.as_view(), name="evidencias"),
    path("evidencias/<int:pk>/", vistas.EvidenciaDetalleVista.as_view(), name="evidencia-detalle"),
    path("evidencias/<int:pk>/ficheros/", vistas.EvidenciaFicheroVista.as_view(), name="evidencia-ficheros"),
    path("evidencias/<int:pk>/fichero/", vistas.EvidenciaFicheroActualVista.as_view(), name="evidencia-fichero-vigente"),
    path("evidencias/<int:pk>/clasificaciones/", vistas.EvidenciaClasificacionesVista.as_view(), name="evidencia-clasificaciones"),
    path("ficheros/<int:pk>/descarga/", vistas.FicheroDescargaVista.as_view(), name="fichero-descarga"),
    path("ciclos/<int:pk>/verificar-huellas/", vistas.CicloVerificacionHuellaVista.as_view(), name="ciclo-verificar-huellas"),
    path("criterios/<str:codigo>/evidencias/", vistas.EvidenciasPorCriterioVista.as_view(), name="criterio-evidencias"),
]
