from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from ciclos.modelos import Ciclo
from ciclos.servicios import exigir_ciclo_abierto
from evidencias.modelos import Evidencia
from nucleo.modelos import ModeloBase
from valoracion.models import Valoracion


class PlanMejora(ModeloBase):
    class Estado(models.TextChoices):
        BORRADOR = "borrador", "Borrador"
        APROBADO = "aprobado", "Aprobado"
        CERRADO = "cerrado", "Cerrado"

    ciclo = models.OneToOneField(
        Ciclo,
        verbose_name="ciclo",
        related_name="plan_mejora",
        on_delete=models.PROTECT,
    )
    estado = models.CharField(
        "estado",
        max_length=20,
        choices=Estado.choices,
        default=Estado.BORRADOR,
    )
    aprobado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="aprobado por",
        related_name="planes_mejora_aprobados",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = "plan de mejora"
        verbose_name_plural = "planes de mejora"

    def __str__(self):
        return f"Plan de mejora del ciclo {self.ciclo}"

    def clean(self):
        super().clean()
        if self.ciclo_id is not None:
            exigir_ciclo_abierto(self.ciclo)
        if self.aprobado_por_id is not None and self.ciclo_id is not None:
            if self.aprobado_por.carrera_id != self.ciclo.carrera_id:
                raise ValidationError({
                    "aprobado_por": "El aprobador debe pertenecer a la misma carrera del ciclo."
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class AccionMejora(ModeloBase):
    class Estado(models.TextChoices):
        PROPUESTA = "propuesta", "Propuesta"
        APROBADA = "aprobada", "Aprobada"
        EN_CURSO = "en_curso", "En curso"
        CUMPLIDA = "cumplida", "Cumplida"
        NO_CUMPLIDA = "no_cumplida", "No cumplida"

    plan = models.ForeignKey(
        PlanMejora,
        verbose_name="plan",
        related_name="acciones",
        on_delete=models.CASCADE,
    )
    debilidad = models.ForeignKey(
        Valoracion,
        verbose_name="debilidad de origen",
        related_name="acciones_mejora",
        limit_choices_to={"tipo": Valoracion.Tipo.DEBILIDAD},
        on_delete=models.PROTECT,
    )
    descripcion = models.TextField("descripción")
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="responsable",
        related_name="acciones_mejora_responsables",
        on_delete=models.PROTECT,
    )
    fecha_limite = models.DateField("fecha límite")
    estado = models.CharField(
        "estado",
        max_length=20,
        choices=Estado.choices,
        default=Estado.PROPUESTA,
    )
    valoracion_resultado = models.TextField("valoración del resultado", blank=True)

    class Meta:
        verbose_name = "acción de mejora"
        verbose_name_plural = "acciones de mejora"

    def __str__(self):
        return f"{self.descripcion[:60]}..."

    def clean(self):
        super().clean()
        if self.plan_id is not None:
            exigir_ciclo_abierto(self.plan.ciclo)
        if self.debilidad_id is not None:
            if self.debilidad.tipo != Valoracion.Tipo.DEBILIDAD:
                raise ValidationError({
                    "debilidad": "La acción de mejora debe originarse en una debilidad de valoración."
                })
            if self.plan_id is not None and self.debilidad.ciclo_id != self.plan.ciclo_id:
                raise ValidationError({
                    "debilidad": "La debilidad debe pertenecer al mismo ciclo que el plan de mejora."
                })
        if self.responsable_id is not None and self.plan_id is not None:
            if getattr(self.responsable, "carrera_id", None) is not None and self.responsable.carrera_id != self.plan.ciclo.carrera_id:
                raise ValidationError({
                    "responsable": "El responsable debe pertenecer a la misma carrera del ciclo."
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class SeguimientoAccion(ModeloBase):
    accion = models.ForeignKey(
        AccionMejora,
        verbose_name="acción",
        related_name="seguimientos",
        on_delete=models.CASCADE,
    )
    fecha = models.DateTimeField("fecha", auto_now_add=True)
    avance = models.PositiveSmallIntegerField("avance (%)", default=0)
    nota = models.TextField("nota", blank=True)
    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="registrado por",
        related_name="seguimientos_acciones",
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = "seguimiento de acción"
        verbose_name_plural = "seguimientos de acción"
        ordering = ("-fecha",)

    def __str__(self):
        return f"Seguimiento de {self.accion_id} ({self.avance}%)"

    def clean(self):
        super().clean()
        if self.accion_id is not None:
            exigir_ciclo_abierto(self.accion.plan.ciclo)
        if self.avance < 0 or self.avance > 100:
            raise ValidationError({"avance": "El avance debe estar entre 0 y 100."})

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError("Los seguimientos no son editables; debe crearse uno nuevo.")
        self.full_clean()
        return super().save(*args, **kwargs)


class AccionEvidencia(ModeloBase):
    accion = models.ForeignKey(
        AccionMejora,
        verbose_name="acción",
        related_name="evidencias",
        on_delete=models.CASCADE,
    )
    evidencia = models.ForeignKey(
        "evidencias.Evidencia",
        verbose_name="evidencia",
        related_name="acciones_mejora",
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = "evidencia de acción"
        verbose_name_plural = "evidencias de acción"
        constraints = [
            models.UniqueConstraint(
                fields=("accion", "evidencia"),
                name="mejora_accion_evidencia_unica",
            )
        ]

    def __str__(self):
        return f"{self.accion} → {self.evidencia}"

    def clean(self):
        super().clean()
        if self.accion_id is not None:
            exigir_ciclo_abierto(self.accion.plan.ciclo)
        if self.accion_id is not None and self.evidencia_id is not None:
            if self.evidencia.ciclo_id != self.accion.plan.ciclo_id:
                raise ValidationError({
                    "evidencia": "La evidencia debe pertenecer al mismo ciclo que la acción de mejora."
                })

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


__all__ = [
    "PlanMejora",
    "AccionMejora",
    "SeguimientoAccion",
    "AccionEvidencia",
]
