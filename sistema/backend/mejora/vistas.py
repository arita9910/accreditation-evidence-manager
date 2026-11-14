from rest_framework import viewsets

from .models import AccionEvidencia, AccionMejora, PlanMejora, SeguimientoAccion
from .serializers import (
    AccionEvidenciaSerializer,
    AccionMejoraSerializer,
    PlanMejoraSerializer,
    SeguimientoAccionSerializer,
)


class PlanMejoraViewSet(viewsets.ModelViewSet):
    queryset = PlanMejora.objects.all()
    serializer_class = PlanMejoraSerializer


class AccionMejoraViewSet(viewsets.ModelViewSet):
    queryset = AccionMejora.objects.all()
    serializer_class = AccionMejoraSerializer


class SeguimientoAccionViewSet(viewsets.ModelViewSet):
    queryset = SeguimientoAccion.objects.all()
    serializer_class = SeguimientoAccionSerializer


class AccionEvidenciaViewSet(viewsets.ModelViewSet):
    queryset = AccionEvidencia.objects.all()
    serializer_class = AccionEvidenciaSerializer
