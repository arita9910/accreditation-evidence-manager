from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from ciclos.modelos import Ciclo
from estructura.models import Criterio, TipoEvidencia

from .modelos import Clasificacion, Evidencia, FicheroEvidencia
from .servicios import clasificar, crear_evidencia, quitar_clasificacion, reemplazar_fichero


def _detalle_validacion(error):
    if hasattr(error, "message_dict"):
        return error.message_dict
    if hasattr(error, "messages"):
        return error.messages
    return [str(error)]


class FicheroEvidenciaSerializador(serializers.ModelSerializer):
    class Meta:
        model = FicheroEvidencia
        fields = (
            "id",
            "evidencia",
            "version",
            "nombre_original",
            "tamano",
            "tipo_mime",
            "sha256",
            "vigente",
            "subido_por",
        )
        read_only_fields = fields


class ClasificacionSerializador(serializers.ModelSerializer):
    criterio = serializers.PrimaryKeyRelatedField(read_only=True)
    clasificada_por = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Clasificacion
        fields = ("id", "evidencia", "criterio", "clasificada_por", "fecha")
        read_only_fields = fields


class EvidenciaSerializador(serializers.ModelSerializer):
    clasificaciones = ClasificacionSerializador(many=True, read_only=True)
    ficheros = FicheroEvidenciaSerializador(many=True, read_only=True)
    fichero_vigente = serializers.SerializerMethodField()
    estado_huella = serializers.SerializerMethodField()

    class Meta:
        model = Evidencia
        fields = (
            "id",
            "ciclo",
            "tipo_evidencia",
            "titulo",
            "descripcion",
            "curso_academico",
            "periodo_desde",
            "periodo_hasta",
            "soporte",
            "custodia_original",
            "clasificaciones",
            "ficheros",
            "fichero_vigente",
            "estado_huella",
        )
        read_only_fields = fields

    def get_fichero_vigente(self, obj):
        fichero = obj.ficheros.filter(vigente=True).order_by("-version").first()
        if fichero is None:
            return None
        return FicheroEvidenciaSerializador(fichero).data

    def get_estado_huella(self, obj):
        fichero = obj.ficheros.filter(vigente=True).order_by("-version").first()
        if fichero is None:
            return None
        from .servicios import verificar_huella

        return verificar_huella(fichero)


class EvidenciaCrearSerializador(serializers.Serializer):
    ciclo = serializers.PrimaryKeyRelatedField(queryset=Ciclo.objects.all())
    tipo_evidencia = serializers.PrimaryKeyRelatedField(queryset=TipoEvidencia.objects.all())
    tipo = serializers.PrimaryKeyRelatedField(queryset=TipoEvidencia.objects.all(), required=False)
    titulo = serializers.CharField(max_length=200)
    descripcion = serializers.CharField(required=False, allow_blank=True, default="")
    curso_academico = serializers.IntegerField()
    periodo_desde = serializers.DateField()
    periodo_hasta = serializers.DateField()
    soporte = serializers.ChoiceField(choices=("digital", "papel"))
    custodia_original = serializers.CharField(required=False, allow_blank=True, default="")
    archivo = serializers.FileField(required=False, allow_null=True)

    def validate(self, attrs):
        if "tipo_evidencia" not in attrs and "tipo" in attrs:
            attrs["tipo_evidencia"] = attrs["tipo"]
        return attrs

    def save(self, **kwargs):
        request = self.context.get("request")
        usuario = self.context.get("usuario") or getattr(request, "user", None)
        try:
            return crear_evidencia(
                self.validated_data["ciclo"],
                {
                    "titulo": self.validated_data["titulo"],
                    "tipo_evidencia": self.validated_data["tipo_evidencia"],
                    "soporte": self.validated_data["soporte"],
                    "curso_academico": self.validated_data["curso_academico"],
                    "periodo_desde": self.validated_data["periodo_desde"],
                    "periodo_hasta": self.validated_data["periodo_hasta"],
                    "descripcion": self.validated_data.get("descripcion", ""),
                    "custodia_original": self.validated_data.get("custodia_original", ""),
                    "usuario": usuario,
                },
                archivo=self.validated_data.get("archivo"),
                usuario=usuario,
            )
        except DjangoValidationError as error:
            raise serializers.ValidationError(_detalle_validacion(error)) from error


class EvidenciaActualizarSerializador(serializers.ModelSerializer):
    class Meta:
        model = Evidencia
        fields = (
            "titulo",
            "descripcion",
            "curso_academico",
            "periodo_desde",
            "periodo_hasta",
            "custodia_original",
            "soporte",
        )

    def update(self, instance, validated_data):
        for campo, valor in validated_data.items():
            setattr(instance, campo, valor)
        instance.full_clean()
        instance.save()
        return instance


class FicheroSubidaSerializador(serializers.Serializer):
    archivo = serializers.FileField()

    def save(self, **kwargs):
        evidencia = self.context["evidencia"]
        request = self.context.get("request")
        usuario = self.context.get("usuario") or getattr(request, "user", None)
        try:
            return reemplazar_fichero(evidencia, self.validated_data["archivo"], usuario=usuario)
        except DjangoValidationError as error:
            raise serializers.ValidationError(_detalle_validacion(error)) from error


class ClasificacionCrearSerializador(serializers.Serializer):
    criterio = serializers.PrimaryKeyRelatedField(queryset=Criterio.objects.all())

    def save(self, **kwargs):
        evidencia = self.context["evidencia"]
        request = self.context.get("request")
        usuario = self.context.get("usuario") or getattr(request, "user", None)
        try:
            return clasificar(evidencia, [self.validated_data["criterio"]], usuario=usuario)
        except DjangoValidationError as error:
            raise serializers.ValidationError(_detalle_validacion(error)) from error


class ClasificacionBorrarSerializador(serializers.Serializer):
    criterio = serializers.PrimaryKeyRelatedField(queryset=Criterio.objects.all())

    def save(self, **kwargs):
        evidencia = self.context["evidencia"]
        request = self.context.get("request")
        usuario = self.context.get("usuario") or getattr(request, "user", None)
        try:
            quitar_clasificacion(evidencia, self.validated_data["criterio"], usuario=usuario)
            return True
        except DjangoValidationError as error:
            raise serializers.ValidationError(_detalle_validacion(error)) from error
