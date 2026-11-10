from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from estructura.models import Dimension, VersionNormativa
from nucleo.modelos import ModeloBase


class Facultad(ModeloBase):
    nombre = models.TextField("nombre")

    class Meta:
        verbose_name = "facultad"
        verbose_name_plural = "facultades"

    def __str__(self):
        return self.nombre


class Carrera(ModeloBase):
    facultad = models.ForeignKey(
        Facultad,
        verbose_name="facultad",
        related_name="carreras",
        on_delete=models.PROTECT,
    )
    nombre = models.TextField("nombre")
    activa = models.BooleanField("activa", default=True)

    class Meta:
        verbose_name = "carrera"
        verbose_name_plural = "carreras"

    def __str__(self):
        return self.nombre


class Ciclo(ModeloBase):
    class Estado(models.TextChoices):
        ABIERTO = "abierto", "Abierto"
        CERRADO = "cerrado", "Cerrado"

    carrera = models.ForeignKey(
        Carrera,
        verbose_name="carrera",
        related_name="ciclos",
        on_delete=models.PROTECT,
    )
    version_normativa = models.ForeignKey(
        VersionNormativa,
        verbose_name="versión normativa",
        related_name="ciclos",
        on_delete=models.PROTECT,
    )
    tipo = models.CharField("tipo", max_length=100)
    anio_base = models.PositiveIntegerField("año base")
    curso_inicial = models.PositiveIntegerField("curso inicial")
    curso_final = models.PositiveIntegerField("curso final")
    estado = models.CharField(
        "estado",
        max_length=10,
        choices=Estado.choices,
        default=Estado.ABIERTO,
    )
    ciclo_anterior = models.ForeignKey(
        "self",
        verbose_name="ciclo anterior",
        related_name="ciclos_siguientes",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    categoria_obtenida = models.TextField("categoría obtenida", null=True, blank=True)
    vigencia_anios = models.PositiveSmallIntegerField(
        "vigencia en años",
        null=True,
        blank=True,
    )
    fecha_apertura = models.DateField("fecha de apertura", default=timezone.localdate)
    fecha_cierre = models.DateField("fecha de cierre", null=True, blank=True)

    class Meta:
        verbose_name = "ciclo"
        verbose_name_plural = "ciclos"
        constraints = [
            models.UniqueConstraint(
                fields=("carrera",),
                condition=Q(estado="abierto"),
                name="ciclos_ciclo_carrera_abierta_unica",
            ),
            models.CheckConstraint(
                condition=Q(curso_final=F("curso_inicial") + 4),
                name="ciclos_ciclo_rango_cinco_cursos",
            ),
            models.CheckConstraint(
                condition=Q(vigencia_anios__isnull=True) | Q(vigencia_anios__in=[5, 7, 9]),
                name="ciclos_ciclo_vigencia_valida",
            ),
        ]

    def __str__(self):
        return f"{self.carrera.nombre} ({self.anio_base})"

    def clean(self):
        super().clean()
        errores = {}

        if self.estado == self.Estado.CERRADO and self.fecha_cierre is None:
            errores["fecha_cierre"] = "Un ciclo cerrado debe tener fecha de cierre."
        if self.estado == self.Estado.ABIERTO and self.fecha_cierre is not None:
            errores["fecha_cierre"] = "Un ciclo abierto no puede tener fecha de cierre."

        if self.ciclo_anterior_id is not None:
            if self.pk is not None and self.ciclo_anterior_id == self.pk:
                errores["ciclo_anterior"] = "El ciclo anterior no puede ser el mismo ciclo."
            else:
                if self.ciclo_anterior.carrera_id != self.carrera_id:
                    errores["ciclo_anterior"] = (
                        "El ciclo anterior debe pertenecer a la misma carrera."
                    )
                elif self.ciclo_anterior.estado != self.Estado.CERRADO:
                    errores["ciclo_anterior"] = "El ciclo anterior debe estar cerrado."

        if self.pk is not None:
            previo = (
                Ciclo.objects.filter(pk=self.pk)
                .only(
                    "carrera_id",
                    "version_normativa_id",
                    "tipo",
                    "anio_base",
                    "curso_inicial",
                    "curso_final",
                    "estado",
                    "ciclo_anterior_id",
                    "categoria_obtenida",
                    "vigencia_anios",
                    "fecha_apertura",
                    "fecha_cierre",
                )
                .first()
            )
            if previo is not None and previo.estado == self.Estado.CERRADO:
                campos_bloqueados = (
                    "carrera_id",
                    "version_normativa_id",
                    "tipo",
                    "anio_base",
                    "curso_inicial",
                    "curso_final",
                    "estado",
                    "ciclo_anterior_id",
                    "categoria_obtenida",
                    "vigencia_anios",
                    "fecha_apertura",
                    "fecha_cierre",
                )
                if any(
                    getattr(self, campo_bloqueado) != getattr(previo, campo_bloqueado)
                    for campo_bloqueado in campos_bloqueados
                ):
                    errores["__all__"] = "Los ciclos cerrados son de solo lectura."

        if errores:
            raise ValidationError(errores)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class AsignacionDimension(ModeloBase):
    ciclo = models.ForeignKey(
        Ciclo,
        verbose_name="ciclo",
        related_name="asignaciones",
        on_delete=models.CASCADE,
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="usuario",
        related_name="asignaciones_dimension",
        on_delete=models.PROTECT,
    )
    dimension = models.ForeignKey(
        Dimension,
        verbose_name="dimensión",
        related_name="asignaciones",
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = "asignación de dimensión"
        verbose_name_plural = "asignaciones de dimensiones"
        constraints = [
            models.UniqueConstraint(
                fields=("ciclo", "usuario", "dimension"),
                name="ciclos_asignacion_dimension_unica",
            )
        ]

    def __str__(self):
        return f"{self.usuario} - {self.dimension} ({self.ciclo})"
