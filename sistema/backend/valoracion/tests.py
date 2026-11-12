from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from ciclos.modelos import Carrera, Ciclo, Facultad
from estructura.models import Criterio, Dimension, Indicador, TipoEvidencia, VersionNormativa
from evidencias.modelos import Evidencia

from .models import Valoracion, ValoracionCriterio, ValoracionEvidencia


class ValoracionModelosTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            "usuario-valoracion",
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
        self.otra_dimension = Dimension.objects.create(
            version=self.version,
            codigo="2",
            nombre="Recursos",
            orden=2,
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
            tipo_dato=Criterio.TipoDato.CUALITATIVO,
            valoracion_por_categoria=False,
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
            titulo="Memoria de autoevaluación",
            descripcion="Documento principal del ciclo",
            curso_academico=2025,
            periodo_desde=date(2025, 9, 1),
            periodo_hasta=date(2026, 6, 30),
            soporte=Evidencia.Soporte.DIGITAL,
        )
        self.valoracion = Valoracion.objects.create(
            ciclo=self.ciclo,
            dimension=self.dimension,
            tipo=Valoracion.Tipo.FORTALEZA,
            texto="La propuesta tiene un enfoque sólido.",
            redactada_por=self.usuario,
        )

    def test_valoracion_acepta_criterios_y_evidencias_del_mismo_ciclo_y_dimension(self):
        ValoracionCriterio.objects.create(
            valoracion=self.valoracion,
            criterio=self.criterio,
        )
        ValoracionEvidencia.objects.create(
            valoracion=self.valoracion,
            evidencia=self.evidencia,
        )

        self.assertEqual(self.valoracion.criterios.count(), 1)
        self.assertEqual(self.valoracion.evidencias.count(), 1)

    def test_criterio_de_otra_dimension_rechaza_relacion(self):
        otro_criterio = Criterio.objects.create(
            indicador=Indicador.objects.create(
                dimension=self.otra_dimension,
                codigo="2.1",
                texto="Indicador ajeno",
            ),
            codigo="2.1.1",
            codigo_guia="C-2",
            solo_en_guia=False,
            texto="Criterio ajeno",
            tipo_dato=Criterio.TipoDato.CUALITATIVO,
            valoracion_por_categoria=False,
        )

        rel = ValoracionCriterio(valoracion=self.valoracion, criterio=otro_criterio)

        with self.assertRaises(ValidationError):
            rel.full_clean()

    def test_evidencia_de_otro_ciclo_rechaza_relacion(self):
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
        otra_evidencia = Evidencia.objects.create(
            ciclo=otro_ciclo,
            tipo_evidencia=self.tipo_evidencia,
            titulo="Evidencia ajena",
            descripcion="No debe asociarse a este ciclo",
            curso_academico=2026,
            periodo_desde=date(2026, 9, 1),
            periodo_hasta=date(2027, 6, 30),
            soporte=Evidencia.Soporte.DIGITAL,
        )

        rel = ValoracionEvidencia(valoracion=self.valoracion, evidencia=otra_evidencia)

        with self.assertRaises(ValidationError):
            rel.full_clean()

    def test_ciclo_cerrado_rechaza_valoracion(self):
        ciclo_cerrado = Ciclo.objects.create(
            carrera=self.carrera,
            version_normativa=self.version,
            tipo="ordinario",
            anio_base=2028,
            curso_inicial=2023,
            curso_final=2027,
            estado=Ciclo.Estado.CERRADO,
            fecha_apertura=date(2028, 1, 1),
            fecha_cierre=date(2028, 12, 1),
        )
        valoracion = Valoracion(
            ciclo=ciclo_cerrado,
            dimension=self.dimension,
            tipo=Valoracion.Tipo.DEBILIDAD,
            texto="No debería poder crearse.",
            redactada_por=self.usuario,
        )

        with self.assertRaises(ValidationError):
            valoracion.full_clean()

    def test_tablas_de_union_rechazan_registros_duplicados(self):
        ValoracionCriterio.objects.create(
            valoracion=self.valoracion,
            criterio=self.criterio,
        )
        ValoracionEvidencia.objects.create(
            valoracion=self.valoracion,
            evidencia=self.evidencia,
        )

        with self.assertRaises(ValidationError):
            ValoracionCriterio(
                valoracion=self.valoracion,
                criterio=self.criterio,
            ).full_clean()

        with self.assertRaises(ValidationError):
            ValoracionEvidencia(
                valoracion=self.valoracion,
                evidencia=self.evidencia,
            ).full_clean()
