from django.contrib import admin
from .models import Facultad, Carrera, Ciclo, AsignacionDimension

admin.site.register(Facultad)
admin.site.register(Carrera)
admin.site.register(Ciclo)
admin.site.register(AsignacionDimension)