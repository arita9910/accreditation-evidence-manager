from django.contrib import admin
from .models import VersionNormativa, Dimension, Indicador, Criterio

admin.site.register(VersionNormativa)
admin.site.register(Dimension)
admin.site.register(Indicador)
admin.site.register(Criterio)