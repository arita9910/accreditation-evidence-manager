from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from estructura.models import Dimension

from .modelos import AsignacionDimension, Ciclo, Facultad, Carrera
from .servicios import (
    abrir_ciclo,
    asignar_dimension,
    cerrar_ciclo,
    crear_carrera,
    crear_facultad,
    quitar_asignacion,
)


def _detalle_validacion(error):
    if hasattr(error, "message_dict"):
        return error.message_dict
    if hasattr(error, "messages"):
        return error.messages
    return [str(error)]


class FacultadSerializador(serializers.ModelSerializer):
    class Meta:
        model = Facultad
        fields = ("id", "nombre")

    def create(self, validated_data):
        try:
            return crear_facultad(validated_data["nombre"])
        except DjangoValidationError as error:
            raise serializers.ValidationError(_detalle_validacion(error)) from error


class CarreraSerializador(serializers.ModelSerializer):
    facultad = serializers.PrimaryKeyRelatedField(queryset=Facultad.objects.all())

    class Meta:
        model = Carrera
        fields = ("id", "facultad", "nombre", "activa")

    def create(self, validated_data):
        try:
            return crear_carrera(
                facultad=validated_data["facultad"],
                nombre=validated_data["nombre"],
                activa=validated_data.get("activa", True),
            )
        except DjangoValidationError as error:
            raise serializers.ValidationError(_detalle_validacion(error)) from error


class CicloSerializador(serializers.ModelSerializer):
    class Meta:
        model = Ciclo
        fields = (
            "id",
            "carrera",
            "version_normativa",
            "tipo",
            "anio_base",
            "curso_inicial",
            "curso_final",
            "estado",
            "ciclo_anterior",
            "categoria_obtenida",
            "vigencia_anios",
            "fecha_apertura",
            "fecha_cierre",
        )
        read_only_fields = (
            "id",
            "curso_final",
            "estado",
            "categoria_obtenida",
            "vigencia_anios",
            "fecha_apertura",
            "fecha_cierre",
        )

    def create(self, validated_data):
        try:
            return abrir_ciclo(
                carrera=validated_data["carrera"],
                tipo=validated_data["tipo"],
                anio_base=validated_data["anio_base"],
                curso_inicial=validated_data["curso_inicial"],
                version_normativa=validated_data["version_normativa"],
                ciclo_anterior=validated_data.get("ciclo_anterior"),
            )
        except DjangoValidationError as error:
            raise serializers.ValidationError(_detalle_validacion(error)) from error


class CicloCierreSerializador(serializers.Serializer):
    categoria_obtenida = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    vigencia_anios = serializers.ChoiceField(
        choices=(5, 7, 9),
        required=False,
        allow_null=True,
    )

    def save(self, **kwargs):
        ciclo = self.context["ciclo"]
        try:
            return cerrar_ciclo(
                ciclo=ciclo,
                categoria_obtenida=self.validated_data.get("categoria_obtenida"),
                vigencia_anios=self.validated_data.get("vigencia_anios"),
            )
        except DjangoValidationError as error:
            raise serializers.ValidationError(_detalle_validacion(error)) from error


class AsignacionDimensionSerializador(serializers.ModelSerializer):
    class Meta:
        model = AsignacionDimension
        fields = ("id", "ciclo", "usuario", "dimension")
        read_only_fields = ("id", "ciclo")


class AsignacionDimensionCrearSerializador(serializers.Serializer):
    usuario = serializers.IntegerField()
    dimension = serializers.IntegerField()

    def validate_usuario(self, value):
        if not get_user_model().objects.filter(pk=value).exists():
            raise serializers.ValidationError("Debe indicarse un usuario válido.")
        return value

    def validate_dimension(self, value):
        if not Dimension.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Debe indicarse una dimensión válida.")
        return value

    def save(self, **kwargs):
        ciclo = self.context["ciclo"]
        usuario = get_user_model().objects.get(pk=self.validated_data["usuario"])
        dimension = Dimension.objects.get(pk=self.validated_data["dimension"])
        try:
            return asignar_dimension(ciclo=ciclo, usuario=usuario, dimension=dimension)
        except DjangoValidationError as error:
            raise serializers.ValidationError(_detalle_validacion(error)) from error


class AsignacionDimensionQuitarSerializador(serializers.Serializer):
    usuario = serializers.IntegerField()
    dimension = serializers.IntegerField()

    def validate_usuario(self, value):
        if not get_user_model().objects.filter(pk=value).exists():
            raise serializers.ValidationError("Debe indicarse un usuario válido.")
        return value

    def validate_dimension(self, value):
        if not Dimension.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Debe indicarse una dimensión válida.")
        return value

    def save(self, **kwargs):
        ciclo = self.context["ciclo"]
        usuario = get_user_model().objects.get(pk=self.validated_data["usuario"])
        dimension = Dimension.objects.get(pk=self.validated_data["dimension"])
        try:
            return quitar_asignacion(ciclo=ciclo, usuario=usuario, dimension=dimension)
        except DjangoValidationError as error:
            raise serializers.ValidationError(_detalle_validacion(error)) from error
