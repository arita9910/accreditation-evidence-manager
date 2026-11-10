from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class RegistroAuditoriaQuerySet(models.QuerySet):
    def update(self, *args, **kwargs):
        raise ValidationError("Los registros de auditoría son de solo inserción.")

    def delete(self, *args, **kwargs):
        raise ValidationError("Los registros de auditoría no pueden eliminarse.")

    def bulk_update(self, *args, **kwargs):
        raise ValidationError("Los registros de auditoría son de solo inserción.")


class RegistroAuditoria(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="usuario",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="registros_auditoria",
    )
    fecha_hora = models.DateTimeField("fecha y hora", default=timezone.now)
    accion = models.CharField("acción", max_length=200)
    entidad = models.CharField("entidad", max_length=200)
    detalle = models.JSONField("detalle", default=dict, blank=True)
    resultado = models.CharField(
        "resultado",
        max_length=20,
        choices=(("correcto", "Correcto"), ("denegado", "Denegado")),
        default="correcto",
    )
    ip = models.GenericIPAddressField("IP", null=True, blank=True)
    contexto = models.JSONField("contexto", default=dict, blank=True)

    objects = RegistroAuditoriaQuerySet.as_manager()

    class Meta:
        verbose_name = "registro de auditoría"
        verbose_name_plural = "registros de auditoría"
        ordering = ["-fecha_hora"]

    def __str__(self):
        return f"{self.accion} ({self.entidad})"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError("Los registros de auditoría son inmutables.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Los registros de auditoría no pueden eliminarse.")
