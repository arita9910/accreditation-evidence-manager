from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from ciclos.modelos import Ciclo
from evidencias.modelos import Evidencia

from .models import AccionEvidencia, AccionMejora, PlanMejora, SeguimientoAccion
from .servicios import (
    aprobar_accion,
    actualizar_accion_mejora,
    actualizar_plan_mejora,
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
    aprobado_por_nombre = serializers.SerializerMethodField()

    def get_aprobado_por_nombre(self, obj):
        if obj.aprobado_por is None:
            return ""
        nombre = " ".join(
            parte
            for parte in [obj.aprobado_por.nombre, obj.aprobado_por.apellidos]
            if parte
        ).strip()
        return nombre or obj.aprobado_por.username

    class Meta:
        model = PlanMejora
        fields = ("id", "ciclo", "estado", "aprobado_por", "aprobado_por_nombre")
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
        ciclo = self.context.get("ciclo")
        if ciclo is None:
            raise serializers.ValidationError("Debe indicar un ciclo válido.")
        try:
            return crear_plan_mejora(ciclo, usuario=usuario)
        except DjangoValidationError as error:
            raise serializers.ValidationError(_detalle_validacion(error)) from error


class PlanMejoraActualizarSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=PlanMejora.Estado.choices, required=False)

    def save(self, **kwargs):
        request = self.context.get("request")
        usuario = self.context.get("usuario") or getattr(request, "user", None)
        plan = self.context["plan"]
        try:
            return actualizar_plan_mejora(
                plan,
                estado=self.validated_data.get("estado"),
                usuario=usuario,
            )
        except DjangoValidationError as error:
            raise serializers.ValidationError(_detalle_validacion(error)) from error


class AccionMejoraSerializer(serializers.ModelSerializer):
    responsable_nombre = serializers.SerializerMethodField()

    def get_responsable_nombre(self, obj):
        if obj.responsable is None:
            return ""
        nombre = " ".join(
            parte
            for parte in [obj.responsable.nombre, obj.responsable.apellidos]
            if parte
        ).strip()
        return nombre or obj.responsable.username

    class Meta:
        model = AccionMejora
        fields = (
            "id",
            "plan",
            "debilidad",
            "descripcion",
            "responsable",
            "responsable_nombre",
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
                accion = actualizar_accion_mejora(
                    accion,
                    descripcion=accion.descripcion,
                    responsable=accion.responsable,
                    fecha_limite=accion.fecha_limite,
                    valoracion_resultado=accion.valoracion_resultado,
                    usuario=usuario,
                )
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
    "PlanMejoraActualizarSerializer",
    "AccionMejoraSerializer",
    "AccionMejoraCrearSerializer",
    "AccionMejoraActualizarSerializer",
    "SeguimientoAccionSerializer",
    "SeguimientoAccionCrearSerializer",
    "AccionEvidenciaSerializer",
    "AccionEvidenciaCrearSerializer",
]
