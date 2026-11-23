from django.conf import settings
from django.db import models

from nucleo.modelos import ModeloBase


SECCIONES_INFORME = (
    "caracterizacion",
    "fortalezas_debilidades",
    "plan_mejora",
    "estrategia_sostenibilidad",
)

SECCIONES_INFORME_DOCUMENTADAS = {
    "caracterizacion": "Caracterización general de la carrera",
    "fortalezas_debilidades": "Fortalezas y debilidades por dimensión",
    "plan_mejora": "Plan de mejora",
    "estrategia_sostenibilidad": "Estrategia de sostenibilidad del claustro",
}


class TextoInforme(ModeloBase):
    ciclo = models.ForeignKey(
        "ciclos.Ciclo",
        verbose_name="ciclo",
        related_name="textos_informe",
        on_delete=models.CASCADE,
    )
    seccion = models.CharField("sección", max_length=100)
    contenido = models.TextField("contenido", blank=True, default="")
    editado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="editado por",
        related_name="textos_informe_editados",
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = "texto de informe"
        verbose_name_plural = "textos de informe"
        constraints = [
            models.UniqueConstraint(
                fields=("ciclo", "seccion"),
                name="informes_texto_ciclo_seccion_unico",
            )
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        super().clean()
        if self.seccion not in SECCIONES_INFORME_DOCUMENTADAS:
            raise ValidationError({"seccion": "La sección del informe no es válida."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class VersionInforme(ModeloBase):
    class MetodoConteo(models.TextChoices):
        LIBREOFFICE = "libreoffice", "LibreOffice"
        ESTIMADO = "estimado", "Estimado"

    ciclo = models.ForeignKey(
        "ciclos.Ciclo",
        verbose_name="ciclo",
        related_name="versiones_informe",
        on_delete=models.CASCADE,
    )
    numero = models.PositiveIntegerField("número")
    fichero = models.CharField("fichero interno", max_length=255)
    sha256 = models.CharField("SHA-256", max_length=64)
    paginas = models.PositiveIntegerField("páginas")
    metodo_conteo = models.CharField(
        "método de conteo",
        max_length=20,
        choices=MetodoConteo.choices,
    )
    avisos = models.JSONField("avisos", default=list, blank=True)

    class Meta:
        verbose_name = "versión de informe"
        verbose_name_plural = "versiones de informe"
        constraints = [
            models.UniqueConstraint(
                fields=("ciclo", "numero"),
                name="informes_version_ciclo_numero_unico",
            )
        ]
        ordering = ("numero",)


__all__ = [
    "SECCIONES_INFORME",
    "SECCIONES_INFORME_DOCUMENTADAS",
    "TextoInforme",
    "VersionInforme",
]
