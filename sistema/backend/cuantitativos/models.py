from django.core.exceptions import ValidationError
from django.db import models

from ciclos.modelos import Ciclo
from estructura.models import Criterio, ModeloCampo
from evidencias.modelos import Evidencia
from nucleo.modelos import ModeloBase


class ValorModelo(ModeloBase):
    ciclo = models.ForeignKey(
        Ciclo,
        verbose_name="ciclo",
        related_name="valores_modelo",
        on_delete=models.PROTECT,
    )
    campo = models.ForeignKey(
        ModeloCampo,
        verbose_name="campo",
        related_name="valores",
        on_delete=models.PROTECT,
    )
    curso = models.PositiveSmallIntegerField("curso")
    valor = models.DecimalField("valor", max_digits=12, decimal_places=4, null=True, blank=True)
    numerador = models.DecimalField(
        "numerador",
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
    )
    denominador = models.DecimalField(
        "denominador",
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "valor de modelo"
        verbose_name_plural = "valores de modelo"
        constraints = [
            models.UniqueConstraint(
                fields=("ciclo", "campo", "curso"),
                name="cuantitativos_valor_modelo_ciclo_campo_curso_unico",
            )
        ]

    def __str__(self):
        return f"{self.ciclo} · {self.campo} · curso {self.curso}"

    def clean(self):
        super().clean()
        if self.ciclo_id is not None and self.campo_id is not None:
            if self.campo.modelo.version_id != self.ciclo.version_normativa_id:
                raise ValidationError({
                    "campo": "El campo debe pertenecer a la misma versión normativa del ciclo."
                })
        for campo, nombre in (
            (self.valor, "valor"),
            (self.numerador, "numerador"),
            (self.denominador, "denominador"),
        ):
            if campo is not None and campo < 0:
                raise ValidationError({nombre: "El valor no puede ser negativo."})
        if self.campo_id is not None and self.campo.tipo_valor == ModeloCampo.TipoValor.PORCENTAJE:
            if self.valor is not None and not 0 <= self.valor <= 100:
                raise ValidationError({"valor": "Los porcentajes deben estar entre 0 y 100."})
        if self.numerador is not None and self.denominador is not None and self.denominador <= 0:
            raise ValidationError({"denominador": "El denominador debe ser mayor que cero."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class ValorCriterio(ModeloBase):
    ciclo = models.ForeignKey(
        Ciclo,
        verbose_name="ciclo",
        related_name="valores_criterio",
        on_delete=models.PROTECT,
    )
    criterio = models.ForeignKey(
        Criterio,
        verbose_name="criterio",
        related_name="valores",
        on_delete=models.PROTECT,
    )
    curso = models.PositiveSmallIntegerField("curso", null=True, blank=True)
    valor = models.DecimalField("valor", max_digits=12, decimal_places=4, null=True, blank=True)
    numerador = models.DecimalField(
        "numerador",
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
    )
    denominador = models.DecimalField(
        "denominador",
        max_digits=12,
        decimal_places=4,
        null=True,
        blank=True,
    )
    unidad = models.CharField("unidad", max_length=50, blank=True)
    observacion = models.TextField("observación", blank=True)

    class Meta:
        verbose_name = "valor de criterio"
        verbose_name_plural = "valores de criterio"
        constraints = [
            models.UniqueConstraint(
                fields=("ciclo", "criterio"),
                name="cuantitativos_valor_criterio_ciclo_criterio_unico",
            )
        ]

    def __str__(self):
        return f"{self.ciclo} · {self.criterio}"

    def clean(self):
        super().clean()
        if self.ciclo_id is not None and self.criterio_id is not None:
            if self.criterio.indicador.dimension.version_id != self.ciclo.version_normativa_id:
                raise ValidationError({
                    "criterio": "El criterio debe pertenecer a la misma versión normativa del ciclo."
                })
            if self.criterio.modelos_relacionados.exists():
                raise ValidationError({
                    "criterio": "Un criterio asociado a un modelo no admite valor propio."
                })
            if self.criterio.tipo_dato == Criterio.TipoDato.CUALITATIVO:
                raise ValidationError({
                    "criterio": "Los criterios cualitativos no admiten valor cuantitativo."
                })
        for campo, nombre in (
            (self.valor, "valor"),
            (self.numerador, "numerador"),
            (self.denominador, "denominador"),
        ):
            if campo is not None and campo < 0:
                raise ValidationError({nombre: "El valor no puede ser negativo."})
        if self.numerador is not None and self.denominador is not None and self.denominador <= 0:
            raise ValidationError({"denominador": "El denominador debe ser mayor que cero."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class VinculoDato(ModeloBase):
    evidencia = models.ForeignKey(
        Evidencia,
        verbose_name="evidencia",
        related_name="vinculos_dato",
        on_delete=models.PROTECT,
    )
    valor_modelo = models.ForeignKey(
        ValorModelo,
        verbose_name="valor de modelo",
        related_name="vinculos",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )
    valor_criterio = models.ForeignKey(
        ValorCriterio,
        verbose_name="valor de criterio",
        related_name="vinculos",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = "vínculo de dato"
        verbose_name_plural = "vínculos de dato"
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(valor_modelo__isnull=False, valor_criterio__isnull=True)
                    | models.Q(valor_modelo__isnull=True, valor_criterio__isnull=False)
                ),
                name="cuantitativos_vinculo_dato_exactamente_uno",
            )
        ]

    def __str__(self):
        return f"Vínculo {self.evidencia}"

    def clean(self):
        super().clean()
        if self.evidencia_id is not None:
            if self.valor_modelo_id is not None and self.valor_modelo.ciclo_id != self.evidencia.ciclo_id:
                raise ValidationError({
                    "valor_modelo": "El valor del modelo y la evidencia deben pertenecer al mismo ciclo."
                })
            if self.valor_criterio_id is not None and self.valor_criterio.ciclo_id != self.evidencia.ciclo_id:
                raise ValidationError({
                    "valor_criterio": "El valor del criterio y la evidencia deben pertenecer al mismo ciclo."
                })
        if (self.valor_modelo_id is None) == (self.valor_criterio_id is None):
            raise ValidationError(
                "Un vínculo de dato debe apuntar a exactamente uno de los dos tipos de dato."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


__all__ = ["ValorModelo", "ValorCriterio", "VinculoDato"]
