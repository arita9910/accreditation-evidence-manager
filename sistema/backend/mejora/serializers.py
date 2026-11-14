from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from ciclos.modelos import Ciclo
from evidencias.modelos import Evidencia

from .models import AccionEvidencia, AccionMejora, PlanMejora, SeguimientoAccion
from .servicios import (
    aprobar_accion,
    cambiar_estado_accion,
    crear_accion_mejora,
    crear_plan_mejora,
    registrar_seguimiento,
    vincular_evidencia,
)


def _detalle_validacion(error):
    if hasattr(error, "message_dict"):
        return error.message_dict
    if hasattr(error, "messages"):
        return error.messages
    return [str(error)]


class PlanMejoraSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanMejora
        fields = ("id", "ciclo", "estado", "aprobado_por")
        read_only_fields = fields


class PlanMejoraCrearSerializer(serializers.Serializer):
    ciclo = serializers.PrimaryKeyRelatedField(queryset=Ciclo.objects.all(), required=False)

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
        ciclo = self.validated_data.get("ciclo") or self.context.get("ciclo")
        try:
            return crear_plan_mejora(ciclo, usuario=usuario)
        except DjangoValidationError as error:
            raise serializers.ValidationError(_detalle_validacion(error)) from error


class AccionMejoraSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccionMejora
        fields = (
            "id",
            "plan",
            "debilidad",
            "descripcion",
            "responsable",
            "fecha_limite",
            "estado",
            "valoracion_resultado",
        )
        read_only_fields = fields


class AccionMejoraCrearSerializer(serializers.Serializer):
    debilidad = serializers.PrimaryKeyRelatedField(queryset=AccionMejora._meta.get_field("debilidad").remote_field.model.objects.all())
    descripcion = serializers.CharField(trim_whitespace=True)
    responsable = serializers.PrimaryKeyRelatedField(queryset=AccionMejora._meta.get_field("responsable").remote_field.model.objects.all())
    fecha_limite = serializers.DateField()

    def save(self, **kwargs):
        request = self.context.get("request")
        usuario = self.context.get("usuario") or getattr(request, "user", None)
        plan = self.context["plan"]
        try:
            return crear_accion_mejora(
                plan,
                self.validated_data["debilidad"],
                self.validated_data["descripcion"],
                self.validated_data["responsable"],
                self.validated_data["fecha_limite"],
                usuario=usuario,
            )
        except DjangoValidationError as error:
            raise serializers.ValidationError(_detalle_validacion(error)) from error


class AccionMejoraActualizarSerializer(serializers.Serializer):
    descripcion = serializers.CharField(trim_whitespace=True, required=False)
    responsable = serializers.PrimaryKeyRelatedField(
        queryset=AccionMejora._meta.get_field("responsable").remote_field.model.objects.all(),
        required=False,
    )
    fecha_limite = serializers.DateField(required=False)
    estado = serializers.ChoiceField(choices=AccionMejora.Estado.choices, required=False)
    valoracion_resultado = serializers.CharField(required=False, allow_blank=True)
    nota = serializers.CharField(required=False, allow_blank=True)

    def save(self, **kwargs):
        request = self.context.get("request")
        usuario = self.context.get("usuario") or getattr(request, "user", None)
        accion = self.context["accion"]

        try:
            if "descripcion" in self.validated_data:
                accion.descripcion = self.validated_data["descripcion"]
            if "responsable" in self.validated_data:
                accion.responsable = self.validated_data["responsable"]
            if "fecha_limite" in self.validated_data:
                accion.fecha_limite = self.validated_data["fecha_limite"]
            if "valoracion_resultado" in self.validated_data:
                accion.valoracion_resultado = self.validated_data["valoracion_resultado"]

            if "estado" in self.validated_data:
                nuevo_estado = self.validated_data["estado"]
                nota = self.validated_data.get("nota")
                if nuevo_estado == AccionMejora.Estado.APROBADA:
                    accion = aprobar_accion(accion, usuario=usuario, nota=nota)
                else:
                    accion = cambiar_estado_accion(accion, nuevo_estado, usuario=usuario, nota=nota)
            else:
                accion.full_clean()
                accion.save()
            return accion
        except DjangoValidationError as error:
            raise serializers.ValidationError(_detalle_validacion(error)) from error


class SeguimientoAccionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SeguimientoAccion
        fields = ("id", "accion", "fecha", "avance", "nota", "registrado_por")
        read_only_fields = fields


class SeguimientoAccionCrearSerializer(serializers.Serializer):
    avance = serializers.IntegerField(min_value=0, max_value=100)
    nota = serializers.CharField(required=False, allow_blank=True)

    def save(self, **kwargs):
        request = self.context.get("request")
        usuario = self.context.get("usuario") or getattr(request, "user", None)
        accion = self.context["accion"]
        try:
            return registrar_seguimiento(
                accion,
                self.validated_data["avance"],
                self.validated_data.get("nota", ""),
                usuario=usuario,
            )
        except DjangoValidationError as error:
            raise serializers.ValidationError(_detalle_validacion(error)) from error


class AccionEvidenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccionEvidencia
        fields = ("id", "accion", "evidencia")
        read_only_fields = fields


class AccionEvidenciaCrearSerializer(serializers.Serializer):
    evidencia = serializers.PrimaryKeyRelatedField(queryset=Evidencia.objects.all())

    def save(self, **kwargs):
        request = self.context.get("request")
        usuario = self.context.get("usuario") or getattr(request, "user", None)
        accion = self.context["accion"]
        try:
            return vincular_evidencia(accion, self.validated_data["evidencia"], usuario=usuario)
        except DjangoValidationError as error:
            raise serializers.ValidationError(_detalle_validacion(error)) from error


__all__ = [
    "PlanMejoraSerializer",
    "PlanMejoraCrearSerializer",
    "AccionMejoraSerializer",
    "AccionMejoraCrearSerializer",
    "AccionMejoraActualizarSerializer",
    "SeguimientoAccionSerializer",
    "SeguimientoAccionCrearSerializer",
    "AccionEvidenciaSerializer",
    "AccionEvidenciaCrearSerializer",
]
