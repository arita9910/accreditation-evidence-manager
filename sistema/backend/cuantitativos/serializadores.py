from rest_framework import serializers

from .models import ValorCriterio, ValorModelo, VinculoDato


class ValorModeloSerializador(serializers.ModelSerializer):
    tipo = serializers.SerializerMethodField()
    modelo = serializers.SerializerMethodField()
    campo = serializers.IntegerField(source="campo_id", read_only=True)
    criterio = serializers.SerializerMethodField()

    class Meta:
        model = ValorModelo
        fields = (
            "id",
            "tipo",
            "modelo",
            "campo",
            "curso",
            "valor",
            "numerador",
            "denominador",
            "criterio",
        )
        read_only_fields = fields

    def get_tipo(self, obj):
        return "modelo"

    def get_modelo(self, obj):
        return getattr(obj.campo.modelo, "numero", None)

    def get_criterio(self, obj):
        return None


class ValorCriterioSerializador(serializers.ModelSerializer):
    tipo = serializers.SerializerMethodField()
    criterio = serializers.SerializerMethodField()
    codigo = serializers.SerializerMethodField()

    class Meta:
        model = ValorCriterio
        fields = (
            "id",
            "tipo",
            "criterio",
            "codigo",
            "curso",
            "valor",
            "numerador",
            "denominador",
            "unidad",
            "observacion",
        )
        read_only_fields = fields

    def get_tipo(self, obj):
        return "criterio"

    def get_criterio(self, obj):
        return obj.criterio_id

    def get_codigo(self, obj):
        return getattr(obj.criterio, "codigo", None)


class VinculoDatoSerializador(serializers.ModelSerializer):
    tipo = serializers.SerializerMethodField()

    class Meta:
        model = VinculoDato
        fields = (
            "id",
            "tipo",
            "evidencia",
            "valor_modelo",
            "valor_criterio",
        )
        read_only_fields = fields

    def get_tipo(self, obj):
        return "modelo" if obj.valor_modelo_id is not None else "criterio"
