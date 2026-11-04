from datetime import date

from django.db import IntegrityError, transaction
from django.test import SimpleTestCase
from django.test import TestCase

from .models import (
    Criterio,
    CriterioModelo,
    Dimension,
    EvidenciaSugerida,
    Indicador,
    ModeloCampo,
    ModeloDefinicion,
    RequisitoCategoria,
    TipoEvidencia,
    VersionNormativa,
)


class ModelosEstructuraStrTests(SimpleTestCase):
    def test_todos_los_modelos_tienen_representacion_informativa(self):
        version = VersionNormativa(nombre="SEA-CU 2025")
        dimension = Dimension(version=version, codigo="1", nombre="Pertinencia")
        indicador = Indicador(dimension=dimension, codigo="1.1", texto="Indicador")
        criterio = Criterio(indicador=indicador, codigo="1.1.1", texto="Criterio")
        modelo = ModeloDefinicion(version=version, numero=1, nombre="Modelo inicial")
        objetos_y_textos = [
            (version, "SEA-CU 2025"),
            (dimension, "1 Pertinencia"),
            (indicador, "1.1 — Indicador"),
            (criterio, "1.1.1 — Criterio"),
            (
                EvidenciaSugerida(criterio=criterio, texto="Acta de reunión"),
                "1.1.1: Acta de reunión",
            ),
            (
                RequisitoCategoria(criterio=criterio, categoria="excelencia"),
                "1.1.1 — Excelencia",
            ),
            (
                TipoEvidencia(dimension=dimension, nombre="Informe"),
                "Informe",
            ),
            (modelo, "Modelo 1: Modelo inicial"),
            (
                ModeloCampo(modelo=modelo, fila=2, columna=3),
                "Modelo 1, fila 2, columna 3",
            ),
            (CriterioModelo(criterio=criterio, modelo=modelo), "1.1.1 — Modelo 1"),
        ]

        for objeto, texto_esperado in objetos_y_textos:
            with self.subTest(modelo=objeto.__class__.__name__):
                self.assertEqual(str(objeto), texto_esperado)


class UnicidadDeCodigosTests(TestCase):
    def setUp(self):
        self.version = self.crear_version("SEA-CU 2025")
        self.otra_version = self.crear_version("SEA-CU 2026")
        self.dimension = self.crear_dimension(self.version, "1")
        self.otra_dimension = self.crear_dimension(self.version, "2")
        self.otro_version_dimension = self.crear_dimension(self.otra_version, "1")
        self.indicador = self.crear_indicador(self.dimension, "1.1")
        self.otro_indicador = self.crear_indicador(self.dimension, "1.2")
        self.otro_padre_indicador = self.crear_indicador(self.otra_dimension, "1.1")

    def crear_version(self, nombre):
        return VersionNormativa.objects.create(
            nombre=nombre,
            fecha_aprobacion=date(2025, 1, 1),
            fuentes="Fuente",
            activa=True,
        )

    def crear_dimension(self, version, codigo):
        return Dimension.objects.create(
            version=version,
            codigo=codigo,
            nombre=f"Dimensión {codigo}",
            orden=1,
        )

    def crear_indicador(self, dimension, codigo):
        return Indicador.objects.create(
            dimension=dimension,
            codigo=codigo,
            texto=f"Indicador {codigo}",
        )

    def crear_criterio(self, indicador, codigo):
        return Criterio.objects.create(
            indicador=indicador,
            codigo=codigo,
            codigo_guia=codigo,
            solo_en_guia=False,
            texto=f"Criterio {codigo}",
            tipo_dato=Criterio.TipoDato.CUALITATIVO,
            valoracion_por_categoria=False,
        )

    def test_dimension_rechaza_codigo_repetido_en_la_misma_version(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.crear_dimension(self.version, "1")

    def test_indicador_rechaza_codigo_repetido_en_la_misma_dimension(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.crear_indicador(self.dimension, "1.1")

    def test_criterio_rechaza_codigo_repetido_en_el_mismo_indicador(self):
        self.crear_criterio(self.indicador, "1.1.1")

        with self.assertRaises(IntegrityError), transaction.atomic():
            self.crear_criterio(self.indicador, "1.1.1")

    def test_permite_codigo_igual_bajo_padres_distintos(self):
        self.crear_dimension(self.version, "3")
        self.crear_criterio(self.indicador, "1.1.1")
        self.crear_criterio(self.otro_indicador, "1.1.1")
        self.crear_criterio(self.otro_padre_indicador, "1.1.1")
