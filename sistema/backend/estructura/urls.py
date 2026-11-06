from django.urls import path

from . import vistas


urlpatterns = [
    path("", vistas.arbol_catalogo, name="arbol-catalogo"),
    path("criterios/<str:codigo>/", vistas.ficha_criterio, name="ficha-criterio"),
    path("modelos/", vistas.lista_modelos, name="lista-modelos"),
    path("versiones/", vistas.lista_versiones, name="lista-versiones"),
]
