from django.db import models

from nucleo.modelos import ModeloBase


class VersionNormativa(ModeloBase):
    nombre = models.TextField("nombre")
    fecha_aprobacion = models.DateField("fecha de aprobación")
    fuentes = models.TextField("fuentes")
    activa = models.BooleanField("activa")

    class Meta:
        verbose_name = "versión normativa"
        verbose_name_plural = "versiones normativas"

    def __str__(self):
        return self.nombre


class Dimension(ModeloBase):
    version = models.ForeignKey(
        VersionNormativa,
        verbose_name="versión",
        related_name="dimensiones",
        on_delete=models.PROTECT,
    )
    codigo = models.TextField("código")
    nombre = models.TextField("nombre")
    orden = models.PositiveIntegerField("orden")

    class Meta:
        verbose_name = "dimensión"
        verbose_name_plural = "dimensiones"
        constraints = [
            models.UniqueConstraint(
                fields=("version", "codigo"),
                name="estructura_dimension_version_codigo_unico",
            )
        ]

    def __str__(self):
        return f"{self.codigo} {self.nombre}"


class Indicador(ModeloBase):
    dimension = models.ForeignKey(
        Dimension,
        verbose_name="dimensión",
        related_name="indicadores",
        on_delete=models.PROTECT,
    )
    codigo = models.TextField("código")
    texto = models.TextField("texto")

    class Meta:
        verbose_name = "indicador"
        verbose_name_plural = "indicadores"
        constraints = [
            models.UniqueConstraint(
                fields=("dimension", "codigo"),
                name="estructura_indicador_dimension_codigo_unico",
            )
        ]

    def __str__(self):
        return f"{self.codigo} — {self.texto}"


class Criterio(ModeloBase):
    class TipoDato(models.TextChoices):
        CUANTITATIVO = "cuantitativo", "Cuantitativo"
        CUALITATIVO = "cualitativo", "Cualitativo"

    indicador = models.ForeignKey(
        Indicador,
        verbose_name="indicador",
        related_name="criterios",
        on_delete=models.PROTECT,
    )
    codigo = models.TextField("código")
    codigo_manual = models.TextField("código del Manual", null=True, blank=True)
    codigo_guia = models.TextField("código de la Guía")
    solo_en_guia = models.BooleanField("solo en la Guía")
    texto = models.TextField("texto")
    tipo_dato = models.CharField("tipo de dato", max_length=12, choices=TipoDato.choices)
    valoracion_por_categoria = models.BooleanField("valoración por categoría")
    nota_normativa = models.TextField("nota normativa", blank=True)

    class Meta:
        verbose_name = "criterio"
        verbose_name_plural = "criterios"
        constraints = [
            models.UniqueConstraint(
                fields=("indicador", "codigo"),
                name="estructura_criterio_indicador_codigo_unico",
            )
        ]

    def __str__(self):
        return f"{self.codigo} — {self.texto}"


class EvidenciaSugerida(ModeloBase):
    criterio = models.ForeignKey(
        Criterio,
        verbose_name="criterio",
        related_name="evidencias_sugeridas",
        on_delete=models.CASCADE,
    )
    texto = models.TextField("texto")
    orden = models.PositiveIntegerField("orden")
    es_verificacion_externa = models.BooleanField("es verificación externa")

    class Meta:
        verbose_name = "evidencia sugerida"
        verbose_name_plural = "evidencias sugeridas"

    def __str__(self):
        return f"{self.criterio.codigo}: {self.texto}"


class RequisitoCategoria(ModeloBase):
    class Categoria(models.TextChoices):
        CALIFICADA = "calificada", "Calificada"
        CERTIFICADA = "certificada", "Certificada"
        EXCELENCIA = "excelencia", "Excelencia"
        UNICA = "unica", "Única"

    criterio = models.ForeignKey(
        Criterio,
        verbose_name="criterio",
        related_name="requisitos_categoria",
        on_delete=models.CASCADE,
    )
    categoria = models.CharField("categoría", max_length=11, choices=Categoria.choices)
    texto = models.TextField("texto")

    class Meta:
        verbose_name = "requisito de categoría"
        verbose_name_plural = "requisitos de categoría"

    def __str__(self):
        return f"{self.criterio.codigo} — {self.get_categoria_display()}"


class TipoEvidencia(ModeloBase):
    class Naturaleza(models.TextChoices):
        DOCUMENTO = "documento", "Documento"
        ACTIVIDAD_VERIFICACION = "actividad_verificacion", "Actividad de verificación"

    class Soporte(models.TextChoices):
        PAPEL_FIRMADO = "papel_firmado", "Papel firmado"
        DIGITAL = "digital", "Digital"
        AMBOS = "ambos", "Ambos"

    dimension = models.ForeignKey(
        Dimension,
        verbose_name="dimensión",
        related_name="tipos_evidencia",
        on_delete=models.PROTECT,
    )
    nombre = models.TextField("nombre")
    descripcion = models.TextField("descripción", blank=True)
    naturaleza = models.CharField("naturaleza", max_length=22, choices=Naturaleza.choices)
    soporte_exigido = models.CharField("soporte exigido", max_length=13, choices=Soporte.choices)

    class Meta:
        verbose_name = "tipo de evidencia"
        verbose_name_plural = "tipos de evidencia"

    def __str__(self):
        return self.nombre


class ModeloDefinicion(ModeloBase):
    version = models.ForeignKey(
        VersionNormativa,
        verbose_name="versión",
        related_name="modelos",
        on_delete=models.PROTECT,
    )
    numero = models.PositiveIntegerField("número")
    numero_rm36 = models.PositiveIntegerField("número RM 36", null=True, blank=True)
    nombre = models.TextField("nombre")

    class Meta:
        verbose_name = "definición de modelo"
        verbose_name_plural = "definiciones de modelo"

    def __str__(self):
        return f"Modelo {self.numero}: {self.nombre}"


class ModeloCampo(ModeloBase):
    class TipoValor(models.TextChoices):
        ENTERO = "entero", "Entero"
        DECIMAL = "decimal", "Decimal"
        PORCENTAJE = "porcentaje", "Porcentaje"
        TEXTO = "texto", "Texto"

    modelo = models.ForeignKey(
        ModeloDefinicion,
        verbose_name="modelo",
        related_name="campos",
        on_delete=models.CASCADE,
    )
    fila = models.PositiveIntegerField("fila")
    columna = models.PositiveIntegerField("columna")
    tipo_valor = models.CharField("tipo de valor", max_length=11, choices=TipoValor.choices)
    orden = models.PositiveIntegerField("orden")

    class Meta:
        verbose_name = "campo de modelo"
        verbose_name_plural = "campos de modelo"

    def __str__(self):
        return f"Modelo {self.modelo.numero}, fila {self.fila}, columna {self.columna}"


class CriterioModelo(ModeloBase):
    criterio = models.ForeignKey(
        Criterio,
        verbose_name="criterio",
        related_name="modelos_relacionados",
        on_delete=models.PROTECT,
    )
    modelo = models.ForeignKey(
        ModeloDefinicion,
        verbose_name="modelo",
        related_name="criterios_relacionados",
        on_delete=models.PROTECT,
    )

    class Meta:
        verbose_name = "relación entre criterio y modelo"
        verbose_name_plural = "relaciones entre criterios y modelos"

    def __str__(self):
        return f"{self.criterio.codigo} — Modelo {self.modelo.numero}"
