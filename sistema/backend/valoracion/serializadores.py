from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from ciclos.modelos import Ciclo
from estructura.models import Dimension

from .models import Valoracion
from .servicios import crear_valoracion, editar_valoracion


def _detalle_validacion(error):
    if hasattr(error, "message_dict"):
        return error.message_dict
    if hasattr(error, "messages"):
        return error.messages
    return [str(error)]


class ValoracionSerializador(serializers.ModelSerializer):
    criterios = serializers.SerializerMethodField()
    evidencias = serializers.SerializerMethodField()
    redactada_por = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Valoracion
        fields = (
            "id",
            "ciclo",
            "dimension",
            "tipo",
            "texto",
            "redactada_por",
            "criterios",
            "evidencias",
        )
        read_only_fields = fields

    def get_criterios(self, obj):
        return list(obj.criterios.values_list("criterio_id", flat=True))

    def get_evidencias(self, obj):
        return list(obj.evidencias.values_list("evidencia_id", flat=True))


class ValoracionCrearSerializador(serializers.Serializer):
    ciclo = serializers.PrimaryKeyRelatedField(queryset=Ciclo.objects.all(), required=False)
    dimension = serializers.PrimaryKeyRelatedField(queryset=Dimension.objects.all())
    tipo = serializers.ChoiceField(choices=Valoracion.Tipo.choices)
    texto = serializers.CharField(trim_whitespace=True)
    criterios = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
    evidencias = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)

    def validate(self, attrs):
        ciclo = self.context.get("ciclo")
        if "ciclo" not in attrs and ciclo is not None:
            attrs["ciclo"] = ciclo
        elif "ciclo" in attrs and ciclo is not None and attrs["ciclo"].pk != ciclo.pk:
            raise serializers.ValidationError("El ciclo indicado no coincide con la URL de la petición.")
        return attrs

    def save(self, **kwargs):
        request = self.context.get("request")
        usuario = self.context.get("usuario") or getattr(request, "user", None)
        try:
            return crear_valoracion(
                ciclo=self.validated_data["ciclo"],
                dimension=self.validated_data["dimension"],
                tipo=self.validated_data["tipo"],
                texto=self.validated_data["texto"],
                criterios=self.validated_data["criterios"],
                evidencias=self.validated_data["evidencias"],
                usuario=usuario,
            )
        except DjangoValidationError as error:
            raise serializers.ValidationError(_detalle_validacion(error)) from error


class ValoracionActualizarSerializador(serializers.Serializer):
    dimension = serializers.PrimaryKeyRelatedField(queryset=Dimension.objects.all(), required=False)
    tipo = serializers.ChoiceField(choices=Valoracion.Tipo.choices, required=False)
    texto = serializers.CharField(trim_whitespace=True, required=False)
    criterios = serializers.ListField(child=serializers.IntegerField(), required=False, allow_empty=False)
    evidencias = serializers.ListField(child=serializers.IntegerField(), required=False, allow_empty=False)

    def save(self, **kwargs):
        request = self.context.get("request")
        usuario = self.context.get("usuario") or getattr(request, "user", None)
        valoracion = self.context["valoracion"]
        try:
            return editar_valoracion(
                valoracion,
                dimension=self.validated_data.get("dimension"),
                tipo=self.validated_data.get("tipo"),
                texto=self.validated_data.get("texto"),
                criterios=self.validated_data.get("criterios"),
                evidencias=self.validated_data.get("evidencias"),
                usuario=usuario,
            )
        except DjangoValidationError as error:
            raise serializers.ValidationError(_detalle_validacion(error)) from error


__all__ = [
    "ValoracionSerializador",
    "ValoracionCrearSerializador",
    "ValoracionActualizarSerializador",
]
