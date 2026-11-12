from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from ciclos.modelos import Carrera, Ciclo, Facultad
from estructura.models import (
    Criterio,
    CriterioModelo,
    Dimension,
    Indicador,
    ModeloCampo,
    ModeloDefinicion,
    TipoEvidencia,
    VersionNormativa,
)
from evidencias.modelos import Evidencia

from .models import ValorCriterio, ValorModelo, VinculoDato


class CuantitativosModelosTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            "usuario-cuantitativos",
            "clave-segura-123",
            nombre="Usuario",
            apellidos="Prueba",
            email="usuario@example.com",
        )
        self.facultad = Facultad.objects.create(nombre="Ingeniería")
        self.carrera = Carrera.objects.create(
            facultad=self.facultad,
            nombre="Ingeniería Informática",
            activa=True,
        )
        self.version = VersionNormativa.objects.create(
            nombre="SEA-CU 2025",
            fecha_aprobacion=date(2025, 1, 1),
            fuentes="Fuente",
            activa=True,
        )
        self.dimension = Dimension.objects.create(
            version=self.version,
            codigo="1",
            nombre="Pertinencia",
            orden=1,
        )
        self.indicador = Indicador.objects.create(
            dimension=self.dimension,
            codigo="1.1",
            texto="Indicador de prueba",
        )
        self.criterio = Criterio.objects.create(
            indicador=self.indicador,
            codigo="1.1.1",
            codigo_guia="C-1",
            solo_en_guia=False,
            texto="Criterio de prueba",
            tipo_dato=Criterio.TipoDato.CUANTITATIVO,
            valoracion_por_categoria=False,
        )
        self.modelo = ModeloDefinicion.objects.create(
            version=self.version,
            numero=1,
            nombre="Modelo de prueba",
        )
        self.campo = ModeloCampo.objects.create(
            modelo=self.modelo,
            fila=1,
            columna=1,
            tipo_valor=ModeloCampo.TipoValor.PORCENTAJE,
            orden=1,
        )
        self.tipo_evidencia = TipoEvidencia.objects.create(
            dimension=self.dimension,
            nombre="Documento de soporte",
            naturaleza=TipoEvidencia.Naturaleza.DOCUMENTO,
            soporte_exigido=TipoEvidencia.Soporte.DIGITAL,
        )
        self.ciclo = Ciclo.objects.create(
            carrera=self.carrera,
            version_normativa=self.version,
            tipo="ordinario",
            anio_base=2026,
            curso_inicial=2021,
            curso_final=2025,
            estado=Ciclo.Estado.ABIERTO,
            fecha_apertura=date(2026, 1, 1),
        )
        self.evidencia = Evidencia.objects.create(
            ciclo=self.ciclo,
            tipo_evidencia=self.tipo_evidencia,
            titulo="Documentación de evidencia",
            descripcion="Documento principal",
            curso_academico="2025-2026",
            periodo_desde=date(2025, 9, 1),
            periodo_hasta=date(2026, 6, 30),
            soporte=Evidencia.Soporte.DIGITAL,
        )

    def test_valor_modelo_rechaza_valores_negativos(self):
        valor = ValorModelo(
            ciclo=self.ciclo,
            campo=self.campo,
            curso=2025,
            valor=-1,
            numerador=2,
            denominador=3,
        )

        with self.assertRaises(ValidationError):
            valor.full_clean()

    def test_valor_modelo_rechaza_porcentaje_fuera_de_rango(self):
        valor = ValorModelo(
            ciclo=self.ciclo,
            campo=self.campo,
            curso=2025,
            valor=110,
            numerador=11,
            denominador=10,
        )

        with self.assertRaises(ValidationError):
            valor.full_clean()

    def test_valor_criterio_rechaza_criterio_que_tiene_modelo_o_es_cualitativo(self):
        CriterioModelo.objects.create(criterio=self.criterio, modelo=self.modelo)

        with self.assertRaises(ValidationError):
            ValorCriterio(
                ciclo=self.ciclo,
                criterio=self.criterio,
                valor=50,
                numerador=5,
                denominador=10,
                unidad="%",
            ).full_clean()

        criterio_cualitativo = Criterio.objects.create(
            indicador=self.indicador,
            codigo="1.1.2",
            codigo_guia="C-2",
            solo_en_guia=False,
            texto="Criterio cualitativo",
            tipo_dato=Criterio.TipoDato.CUALITATIVO,
            valoracion_por_categoria=False,
        )

        with self.assertRaises(ValidationError):
            ValorCriterio(
                ciclo=self.ciclo,
                criterio=criterio_cualitativo,
                valor=1,
                numerador=1,
                denominador=1,
                unidad="puntos",
            ).full_clean()

    def test_vinculo_dato_rechaza_dos_datos_a_la_vez(self):
        valor_modelo = ValorModelo.objects.create(
            ciclo=self.ciclo,
            campo=self.campo,
            curso=2025,
            valor=75,
            numerador=3,
            denominador=4,
        )
        valor_criterio = ValorCriterio.objects.create(
            ciclo=self.ciclo,
            criterio=self.criterio,
            valor=25,
            numerador=1,
            denominador=4,
            unidad="%",
        )

        with self.assertRaises(ValidationError):
            VinculoDato(
                evidencia=self.evidencia,
                valor_modelo=valor_modelo,
                valor_criterio=valor_criterio,
            ).full_clean()

    def test_vinculo_dato_requiere_mismo_ciclo_entre_dato_y_evidencia(self):
        otra_carrera = Carrera.objects.create(
            facultad=self.facultad,
            nombre="Arquitectura",
            activa=True,
        )
        otro_ciclo = Ciclo.objects.create(
            carrera=otra_carrera,
            version_normativa=self.version,
            tipo="ordinario",
            anio_base=2027,
            curso_inicial=2022,
            curso_final=2026,
            estado=Ciclo.Estado.ABIERTO,
            fecha_apertura=date(2027, 1, 1),
        )
        valor_modelo = ValorModelo.objects.create(
            ciclo=otro_ciclo,
            campo=self.campo,
            curso=2025,
            valor=75,
            numerador=3,
            denominador=4,
        )

        with self.assertRaises(ValidationError):
            VinculoDato(
                evidencia=self.evidencia,
                valor_modelo=valor_modelo,
            ).full_clean()

    def test_valores_modelo_y_criterio_tienen_unicidad_por_ciclo_y_relacion(self):
        ValorModelo.objects.create(
            ciclo=self.ciclo,
            campo=self.campo,
            curso=2025,
            valor=80,
            numerador=4,
            denominador=5,
        )
        ValorCriterio.objects.create(
            ciclo=self.ciclo,
            criterio=self.criterio,
            valor=20,
            numerador=1,
            denominador=5,
            unidad="%",
        )

        duplicado_modelo = ValorModelo(
            ciclo=self.ciclo,
            campo=self.campo,
            curso=2025,
            valor=50,
        )
        duplicado_criterio = ValorCriterio(
            ciclo=self.ciclo,
            criterio=self.criterio,
            valor=10,
            numerador=1,
            denominador=10,
            unidad="%",
        )

        with self.assertRaises(ValidationError):
            duplicado_modelo.full_clean()

        with self.assertRaises(ValidationError):
            duplicado_criterio.full_clean()
