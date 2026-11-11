import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from ciclos.modelos import Ciclo
from ciclos.servicios import exigir_ciclo_abierto
from estructura.models import Criterio, TipoEvidencia
from nucleo.modelos import ModeloBase


class Evidencia(ModeloBase):
    class Soporte(models.TextChoices):
        DIGITAL = "digital", "Digital"
        PAPEL = "papel", "Papel"

    ciclo = models.ForeignKey(
        Ciclo,
        verbose_name="ciclo",
        related_name="evidencias",
        on_delete=models.PROTECT,
    )
    tipo_evidencia = models.ForeignKey(
        TipoEvidencia,
        verbose_name="tipo de evidencia",
        related_name="evidencias",
        on_delete=models.PROTECT,
    )
    titulo = models.CharField("título", max_length=200)
    descripcion = models.TextField("descripción", blank=True)
    curso_academico = models.PositiveIntegerField("curso académico")
    periodo_desde = models.DateField("periodo desde")
    periodo_hasta = models.DateField("periodo hasta")
    soporte = models.CharField(
        "soporte",
        max_length=10,
        choices=Soporte.choices,
    )
    custodia_original = models.TextField("custodia original", blank=True)

    class Meta:
        verbose_name = "evidencia"
        verbose_name_plural = "evidencias"

    def __str__(self):
        return self.titulo

    def clean(self):
        super().clean()
        if self.ciclo_id is not None:
            exigir_ciclo_abierto(self.ciclo)
        if self.periodo_desde and self.periodo_hasta and self.periodo_desde > self.periodo_hasta:
            raise ValidationError({
                "periodo_desde": "La fecha de inicio no puede ser posterior a la fecha de fin.",
                "periodo_hasta": "La fecha de fin no puede ser anterior a la fecha de inicio.",
            })
        if self.soporte == self.Soporte.PAPEL:
            if not (self.custodia_original or "").strip():
                raise ValidationError({
                    "custodia_original": "La custodia original es obligatoria para evidencias en papel."
                })
            if self.pk is not None and self.ficheros.exists():
                raise ValidationError("La evidencia en papel no admite ficheros asociados.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class FicheroEvidencia(ModeloBase):
    evidencia = models.ForeignKey(
        Evidencia,
        verbose_name="evidencia",
        related_name="ficheros",
        on_delete=models.CASCADE,
    )
    version = models.PositiveIntegerField("versión")
    nombre_original = models.TextField("nombre original")
    nombre_interno = models.UUIDField("nombre interno", default=uuid.uuid4, unique=True)
    tamano = models.BigIntegerField("tamaño")
    tipo_mime = models.CharField("tipo MIME", max_length=200)
    sha256 = models.CharField("huella SHA-256", max_length=64)
    vigente = models.BooleanField("vigente", default=True)
    subido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="subido por",
        related_name="ficheros_subidos",
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = "fichero de evidencia"
        verbose_name_plural = "ficheros de evidencia"
        constraints = [
            models.UniqueConstraint(
                fields=("evidencia", "version"),
                name="evidencias_fichero_evidencia_version_unica",
            ),
            models.UniqueConstraint(
                fields=("evidencia",),
                condition=Q(vigente=True),
                name="evidencias_fichero_evidencia_vigente_unica",
            ),
        ]

    def __str__(self):
        return f"{self.evidencia.titulo} v{self.version}"

    def clean(self):
        super().clean()
        if self.evidencia_id is not None:
            exigir_ciclo_abierto(self.evidencia.ciclo)
            if self.evidencia.soporte == Evidencia.Soporte.PAPEL:
                raise ValidationError("La evidencia en papel no admite ficheros asociados.")
        if self.vigente and self.evidencia_id is not None:
            existe_vigente = (
                FicheroEvidencia.objects.filter(evidencia=self.evidencia, vigente=True)
                .exclude(pk=self.pk)
                .exists()
            )
            if existe_vigente:
                raise ValidationError("Ya existe un fichero vigente para esta evidencia.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Clasificacion(ModeloBase):
    evidencia = models.ForeignKey(
        Evidencia,
        verbose_name="evidencia",
        related_name="clasificaciones",
        on_delete=models.CASCADE,
    )
    criterio = models.ForeignKey(
        Criterio,
        verbose_name="criterio",
        related_name="clasificaciones",
        on_delete=models.PROTECT,
    )
    clasificada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="clasificada por",
        related_name="clasificaciones_realizadas",
        on_delete=models.PROTECT,
    )
    fecha = models.DateTimeField("fecha", default=timezone.now)

    class Meta:
        verbose_name = "clasificación"
        verbose_name_plural = "clasificaciones"
        constraints = [
            models.UniqueConstraint(
                fields=("evidencia", "criterio"),
                name="evidencias_clasificacion_evidencia_criterio_unica",
            )
        ]

    def __str__(self):
        return f"{self.evidencia.titulo} → {self.criterio.codigo}"

    def clean(self):
        super().clean()
        if self.evidencia_id is not None:
            exigir_ciclo_abierto(self.evidencia.ciclo)
        if self.evidencia_id is not None and self.criterio_id is not None:
            if self.criterio.indicador.dimension.version_id != self.evidencia.ciclo.version_normativa_id:
                raise ValidationError(
                    "El criterio debe pertenecer a la misma versión normativa del ciclo de la evidencia."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


__all__ = ["Evidencia", "FicheroEvidencia", "Clasificacion"]
