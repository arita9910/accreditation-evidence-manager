from rest_framework import serializers

from .models import (
    Criterio,
    Dimension,
    EvidenciaSugerida,
    Indicador,
    ModeloCampo,
    ModeloDefinicion,
    RequisitoCategoria,
    VersionNormativa,
)


class VersionNormativaSerializador(serializers.ModelSerializer):
    class Meta:
        model = VersionNormativa
        fields = ("id", "nombre", "fecha_aprobacion", "fuentes", "activa")
        read_only_fields = fields


class EvidenciaSugeridaSerializador(serializers.ModelSerializer):
    class Meta:
        model = EvidenciaSugerida
        fields = ("texto", "orden", "es_verificacion_externa")
        read_only_fields = fields


class RequisitoCategoriaSerializador(serializers.ModelSerializer):
    class Meta:
        model = RequisitoCategoria
        fields = ("categoria", "texto")
        read_only_fields = fields


class ModeloCampoSerializador(serializers.ModelSerializer):
    class Meta:
        model = ModeloCampo
        fields = ("fila", "columna", "tipo_valor", "orden")
        read_only_fields = fields


class CriterioSerializador(serializers.ModelSerializer):
    evidencias = EvidenciaSugeridaSerializador(
        source="evidencias_sugeridas", many=True, read_only=True
    )
    requisitos_por_categoria = RequisitoCategoriaSerializador(
        source="requisitos_categoria", many=True, read_only=True
    )
    modelos = serializers.SerializerMethodField()

    class Meta:
        model = Criterio
        fields = (
            "id",
            "codigo",
            "codigo_manual",
            "codigo_guia",
            "solo_en_guia",
            "texto",
            "tipo_dato",
            "valoracion_por_categoria",
            "nota_normativa",
            "evidencias",
            "requisitos_por_categoria",
            "modelos",
        )
        read_only_fields = fields

    def get_modelos(self, criterio):
        return [
            {
                "numero": relacion.modelo.numero,
                "numero_rm36": relacion.modelo.numero_rm36,
                "nombre": relacion.modelo.nombre,
            }
            for relacion in criterio.modelos_relacionados.all()
        ]


class IndicadorSerializador(serializers.ModelSerializer):
    criterios = CriterioSerializador(many=True, read_only=True)

    class Meta:
        model = Indicador
        fields = ("id", "codigo", "texto", "criterios")
        read_only_fields = fields


class DimensionSerializador(serializers.ModelSerializer):
    indicadores = IndicadorSerializador(many=True, read_only=True)

    class Meta:
        model = Dimension
        fields = ("id", "codigo", "nombre", "orden", "indicadores")
        read_only_fields = fields


class ModeloDefinicionSerializador(serializers.ModelSerializer):
    campos = ModeloCampoSerializador(many=True, read_only=True)

    class Meta:
        model = ModeloDefinicion
        fields = ("numero", "numero_rm36", "nombre", "campos")
        read_only_fields = fields
