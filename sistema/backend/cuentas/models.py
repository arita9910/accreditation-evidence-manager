from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("El nombre de usuario es obligatorio.")

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

        if extra_fields["is_staff"] is not True:
            raise ValueError("Un superusuario debe tener is_staff=True.")
        if extra_fields["is_superuser"] is not True:
            raise ValueError("Un superusuario debe tener is_superuser=True.")

        return self.create_user(username, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    username = models.CharField("nombre de usuario", max_length=150, unique=True)
    nombre = models.CharField("nombre", max_length=150)
    apellidos = models.CharField("apellidos", max_length=150)
    email = models.EmailField("correo electrónico")
    activo = models.BooleanField("activo", default=True)
    is_staff = models.BooleanField("acceso al administrador", default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["nombre", "apellidos", "email"]

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self):
        return self.username

    @property
    def is_active(self):
        return self.activo

    @is_active.setter
    def is_active(self, value):
        self.activo = value
