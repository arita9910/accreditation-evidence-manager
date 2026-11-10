from rest_framework import serializers

from .modelos import RegistroAuditoria


class RegistroAuditoriaSerializer(serializers.ModelSerializer):
    usuario = serializers.SerializerMethodField()

    class Meta:
        model = RegistroAuditoria
        fields = [
            "id",
            "usuario",
            "fecha_hora",
            "accion",
            "entidad",
            "detalle",
            "resultado",
            "ip",
            "contexto",
        ]

    def get_usuario(self, obj):
        return obj.usuario.username if obj.usuario else None
