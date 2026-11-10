from django.urls import path

from .vistas import listar_auditoria

urlpatterns = [
    path("", listar_auditoria, name="auditoria-lista"),
]
