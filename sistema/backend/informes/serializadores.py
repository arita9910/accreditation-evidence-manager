from rest_framework import serializers

from .modelos import SECCIONES_INFORME_DOCUMENTADAS, TextoInforme, VersionInforme


class TextoInformeSerializador(serializers.ModelSerializer):
    class Meta:
        model = TextoInforme
        fields = ("id", "ciclo", "seccion", "contenido", "editado_por")
        read_only_fields = ("id", "ciclo", "seccion", "editado_por")


class TextoInformeActualizarSerializador(serializers.Serializer):
    contenido = serializers.CharField(allow_blank=True)


class VersionInformeSerializador(serializers.ModelSerializer):
    class Meta:
        model = VersionInforme
        fields = (
            "id",
            "ciclo",
            "numero",
            "sha256",
            "paginas",
            "metodo_conteo",
            "avisos",
        )
        read_only_fields = fields


__all__ = [
    "TextoInformeSerializador",
    "TextoInformeActualizarSerializador",
    "VersionInformeSerializador",
]
