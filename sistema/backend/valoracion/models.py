from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from ciclos.modelos import Ciclo
from ciclos.servicios import exigir_ciclo_abierto
from estructura.models import Criterio, Dimension
from evidencias.modelos import Evidencia
from nucleo.modelos import ModeloBase


class Valoracion(ModeloBase):
    class Tipo(models.TextChoices):
        FORTALEZA = "fortaleza", "Fortaleza"
        DEBILIDAD = "debilidad", "Debilidad"

    ciclo = models.ForeignKey(
        Ciclo,
        verbose_name="ciclo",
        related_name="valoraciones",
        on_delete=models.PROTECT,
    )
    dimension = models.ForeignKey(
        Dimension,
        verbose_name="dimensión",
        related_name="valoraciones",
        on_delete=models.PROTECT,
    )
    tipo = models.CharField(
        "tipo",
        max_length=10,
        choices=Tipo.choices,
    )
    texto = models.TextField("texto")
    redactada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="redactada por",
        related_name="valoraciones_redactadas",
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = "valoración"
        verbose_name_plural = "valoraciones"

    def __str__(self):
        return f"{self.get_tipo_display()} ({self.dimension})"

    def clean(self):
        super().clean()
        if self.ciclo_id is not None:
            exigir_ciclo_abierto(self.ciclo)
        if self.dimension_id is not None and self.ciclo_id is not None:
            if self.dimension.version_id != self.ciclo.version_normativa_id:
                raise ValidationError(
                    {
                        "dimension": "La dimensión debe pertenecer a la misma versión normativa del ciclo."
                    }
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class ValoracionCriterio(ModeloBase):
    valoracion = models.ForeignKey(
        Valoracion,
        verbose_name="valoración",
        related_name="criterios",
        on_delete=models.CASCADE,
    )
    criterio = models.ForeignKey(
        Criterio,
        verbose_name="criterio",
        related_name="valoraciones",
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = "criterio de valoración"
        verbose_name_plural = "criterios de valoración"
        constraints = [
            models.UniqueConstraint(
                fields=("valoracion", "criterio"),
                name="valoracion_criterio_valoracion_criterio_unico",
            )
        ]

    def __str__(self):
        return f"{self.valoracion} → {self.criterio}"

    def clean(self):
        super().clean()
        if self.valoracion_id is not None:
            exigir_ciclo_abierto(self.valoracion.ciclo)
        if self.valoracion_id is not None and self.criterio_id is not None:
            if self.criterio.indicador.dimension_id != self.valoracion.dimension_id:
                raise ValidationError(
                    {
                        "criterio": "El criterio debe pertenecer a la misma dimensión de la valoración."
                    }
                )
            if self.criterio.indicador.dimension.version_id != self.valoracion.ciclo.version_normativa_id:
                raise ValidationError(
                    {
                        "criterio": "El criterio debe pertenecer a la misma versión normativa del ciclo."
                    }
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class ValoracionEvidencia(ModeloBase):
    valoracion = models.ForeignKey(
        Valoracion,
        verbose_name="valoración",
        related_name="evidencias",
        on_delete=models.CASCADE,
    )
    evidencia = models.ForeignKey(
        Evidencia,
        verbose_name="evidencia",
        related_name="valoraciones",
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = "evidencia de valoración"
        verbose_name_plural = "evidencias de valoración"
        constraints = [
            models.UniqueConstraint(
                fields=("valoracion", "evidencia"),
                name="valoracion_evidencia_valoracion_evidencia_unico",
            )
        ]

    def __str__(self):
        return f"{self.valoracion} → {self.evidencia}"

    def clean(self):
        super().clean()
        if self.valoracion_id is not None:
            exigir_ciclo_abierto(self.valoracion.ciclo)
        if self.valoracion_id is not None and self.evidencia_id is not None:
            if self.evidencia.ciclo_id != self.valoracion.ciclo_id:
                raise ValidationError(
                    {
                        "evidencia": "La evidencia debe pertenecer al mismo ciclo que la valoración."
                    }
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


__all__ = ["Valoracion", "ValoracionCriterio", "ValoracionEvidencia"]
