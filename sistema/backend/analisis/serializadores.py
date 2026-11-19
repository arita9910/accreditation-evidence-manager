from rest_framework import serializers


class CriterioEstadoSerializador(serializers.Serializer):
    id = serializers.IntegerField()
    codigo = serializers.CharField()
    codigo_manual = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    nombre = serializers.CharField()
    evidencias_clasificadas = serializers.IntegerField()
    datos_cuantitativos = serializers.BooleanField()
    dato_con_respaldo = serializers.BooleanField()
    tiene_valoracion = serializers.BooleanField()
    tiene_accion = serializers.BooleanField()


class IndicadorEstadoSerializador(serializers.Serializer):
    id = serializers.IntegerField()
    codigo = serializers.CharField()
    nombre = serializers.CharField()
    criterios = CriterioEstadoSerializador(many=True)


class DimensionEstadoSerializador(serializers.Serializer):
    id = serializers.IntegerField()
    codigo = serializers.CharField()
    nombre = serializers.CharField()
    indicadores = IndicadorEstadoSerializador(many=True)


class EstadoCicloSerializador(serializers.Serializer):
    ciclo_id = serializers.IntegerField()
    dimensiones = DimensionEstadoSerializador(many=True)


class CompletitudSerializador(serializers.Serializer):
    ciclo_id = serializers.IntegerField()
    criterios_sin_evidencia = serializers.ListField(child=serializers.IntegerField())
    criterios_cuantitativos_sin_dato = serializers.ListField(child=serializers.IntegerField())
    datos_sin_respaldo = serializers.ListField(child=serializers.DictField())
    modelos_incompletos = serializers.ListField(child=serializers.DictField())
    dimensiones_sin_valoracion = serializers.ListField(child=serializers.IntegerField())
    debilidades_sin_accion = serializers.ListField(child=serializers.IntegerField())


class ComparacionSerializador(serializers.Serializer):
    ciclo_a_id = serializers.IntegerField()
    ciclo_b_id = serializers.IntegerField()
    diferencias_modelos = serializers.ListField(child=serializers.DictField())
    diferencias_criterios = serializers.ListField(child=serializers.DictField())
    diferencias_acciones = serializers.ListField(child=serializers.DictField())


class ErrorSerializador(serializers.Serializer):
    codigo = serializers.CharField()
    mensaje = serializers.CharField()
    detalle = serializers.JSONField()
