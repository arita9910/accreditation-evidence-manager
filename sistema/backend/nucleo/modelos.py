from django.conf import settings
from django.db import models


class ModeloBase(models.Model):
    creado_en = models.DateTimeField("creado en", auto_now_add=True)
    modificado_en = models.DateTimeField("modificado en", auto_now=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="creado por",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="+",
    )
    modificado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="modificado por",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="+",
    )

    class Meta:
        abstract = True
