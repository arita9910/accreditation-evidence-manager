from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from ciclos.modelos import Carrera
from .modelos import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=False)
    carrera = serializers.PrimaryKeyRelatedField(
        queryset=Carrera.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Usuario
        fields = (
            "id",
            "username",
            "nombre",
            "apellidos",
            "email",
            "activo",
            "rol",
            "carrera",
            "password",
        )

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        if password is None:
            raise serializers.ValidationError({"password": "La contraseña es obligatoria."})
        return Usuario.objects.create_user(password=password, **validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if password is not None:
            instance.set_password(password)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.full_clean()
        instance.save()
        return instance


class UsuarioPerfilSerializer(serializers.ModelSerializer):
    permisos = serializers.SerializerMethodField()
    carrera = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Usuario
        fields = (
            "id",
            "username",
            "nombre",
            "apellidos",
            "email",
            "activo",
            "rol",
            "carrera",
            "permisos",
        )

    def get_permisos(self, obj):
        permisos = []
        for accion in (
            "consultar_auditoria",
            "listar_auditoria",
            "abrir_ciclo",
            "cerrar_ciclo",
            "asignar_dimension",
            "listar_usuarios",
            "crear_usuario",
            "editar_usuario",
            "eliminar_usuario",
            "gestionar_usuarios",
            "gestionar_roles",
        ):
            if obj is not None and getattr(obj, "is_authenticated", False) and getattr(obj, "rol", None) == Usuario.Rol.ADMINISTRADOR_TECNICO:
                permisos.append(accion)
                continue
            try:
                from cuentas.permisos import puede

                if puede(obj, accion):
                    permisos.append(accion)
            except Exception:
                pass
        return permisos
