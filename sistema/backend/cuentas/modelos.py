from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models

from nucleo.modelos import ModeloBase


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("El nombre de usuario es obligatorio.")

        if password is None:
            raise ValueError("La contraseña es obligatoria.")

        extra_fields["email"] = self.normalize_email(extra_fields.get("email"))
        user = self.model(
            username=self.model.normalize_username(username),
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("activo", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Un superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Un superusuario debe tener is_superuser=True.")

        return self.create_user(username, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    class Rol(models.TextChoices):
        ADMINISTRADOR_TECNICO = "administrador_tecnico", "Administrador Técnico"
        DIRECTOR_CARRERA = "director_carrera", "Director de Carrera"
        PAR_EVALUADOR = "par_evaluador", "Par evaluador externo"

    username = models.CharField("nombre de usuario", max_length=150, unique=True)
    nombre = models.CharField("nombre", max_length=150)
    apellidos = models.CharField("apellidos", max_length=150)
    email = models.EmailField("correo electrónico")
    activo = models.BooleanField("activo", default=True)
    is_staff = models.BooleanField("acceso al administrador", default=False)
    rol = models.CharField(
        "rol",
        max_length=30,
        choices=Rol.choices,
        default=Rol.ADMINISTRADOR_TECNICO,
    )
    carrera = models.ForeignKey(
        "ciclos.Carrera",
        verbose_name="carrera",
        related_name="usuarios",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    objects = UsuarioManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["nombre", "apellidos", "email"]

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    rol="administrador_tecnico",
                    carrera__isnull=True,
                )
                | models.Q(
                    rol="director_carrera",
                    carrera__isnull=False,
                )
                | models.Q(
                    rol="par_evaluador",
                    carrera__isnull=True,
                ),
                name="cuentas_usuario_rol_carrera_consistente",
                violation_error_message="La relación entre el rol y la carrera no es consistente.",
            )
        ]

    def clean(self):
        super().clean()
        if self.rol == self.Rol.ADMINISTRADOR_TECNICO and self.carrera_id is not None:
            raise ValidationError(
                {"carrera": "Un administrador técnico no puede tener carrera asociada."}
            )
        if self.rol == self.Rol.DIRECTOR_CARRERA and self.carrera_id is None:
            raise ValidationError(
                {"carrera": "Un director de carrera debe tener una carrera asociada."}
            )
        if self.rol == self.Rol.PAR_EVALUADOR and self.carrera_id is not None:
            raise ValidationError(
                {"carrera": "Un par evaluador externo no puede tener una carrera directa."}
            )

    def save(self, *args, **kwargs):
        update_fields = kwargs.get("update_fields")
        if update_fields is not None:
            campos = {str(campo) for campo in update_fields}
            if campos.issubset({"last_login"}):
                return super().save(*args, **kwargs)
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.username

    @property
    def is_active(self):
        return self.activo

    @is_active.setter
    def is_active(self, value):
        self.activo = value


class AsignacionParEvaluador(ModeloBase):
    usuario = models.ForeignKey(
        "cuentas.Usuario",
        verbose_name="par evaluador",
        related_name="asignaciones_par_evaluador",
        on_delete=models.PROTECT,
    )
    ciclo = models.ForeignKey(
        "ciclos.Ciclo",
        verbose_name="ciclo",
        related_name="asignaciones_par_evaluador",
        on_delete=models.CASCADE,
    )
    vigente_desde = models.DateField("vigente desde")
    vigente_hasta = models.DateField("vigente hasta", null=True, blank=True)

    class Meta:
        verbose_name = "asignación de par evaluador"
        verbose_name_plural = "asignaciones de pares evaluadores"
        constraints = [
            models.UniqueConstraint(
                fields=("usuario", "ciclo"),
                name="cuentas_asignacion_par_evaluador_unica",
            ),
            models.CheckConstraint(
                condition=models.Q(vigente_hasta__isnull=True)
                | models.Q(vigente_hasta__gte=models.F("vigente_desde")),
                name="cuentas_asignacion_vigencia_valida",
                violation_error_message="vigente_hasta debe ser posterior o igual a vigente_desde.",
            ),
        ]

    def clean(self):
        super().clean()
        if getattr(self.usuario, "rol", None) != Usuario.Rol.PAR_EVALUADOR:
            raise ValidationError({"usuario": "El usuario debe tener el rol par_evaluador."})
        if self.vigente_hasta is not None and self.vigente_hasta < self.vigente_desde:
            raise ValidationError({"vigente_hasta": "La vigencia final no puede preceder a la inicial."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def esta_vigente(self, fecha=None):
        from django.utils import timezone

        fecha = fecha or timezone.localdate()
        return self.vigente_desde <= fecha and (
            self.vigente_hasta is None or fecha <= self.vigente_hasta
        )

    def __str__(self):
        return f"{self.usuario} - {self.ciclo}"


__all__ = ["Usuario", "UsuarioManager", "AsignacionParEvaluador"]