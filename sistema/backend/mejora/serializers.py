from rest_framework import serializers

from .models import AccionEvidencia, AccionMejora, PlanMejora, SeguimientoAccion


class PlanMejoraSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanMejora
        fields = "__all__"


class AccionMejoraSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccionMejora
        fields = "__all__"


class SeguimientoAccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeguimientoAccion
        fields = "__all__"


class AccionEvidenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccionEvidencia
        fields = "__all__"
