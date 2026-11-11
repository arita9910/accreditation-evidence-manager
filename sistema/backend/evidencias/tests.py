from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from ciclos.modelos import Carrera, Ciclo, Facultad
from estructura.models import Criterio, Dimension, Indicador, TipoEvidencia, VersionNormativa

from .modelos import Clasificacion, Evidencia, FicheroEvidencia


class EvidenciasModelosTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            "usuario-evidencia",
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
            codigo="I1",
            texto="Indicador de prueba",
        )
        self.criterio = Criterio.objects.create(
            indicador=self.indicador,
            codigo="C1",
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

    def test_evidencia_crea_relaciones_y_fichero_vigente_unico(self):
        evidencia = Evidencia.objects.create(
            ciclo=self.ciclo,
            tipo_evidencia=self.tipo_evidencia,
            titulo="Memoria de autoevaluación",
            descripcion="Documento principal del ciclo",
            curso_academico=2025,
            periodo_desde=date(2025, 9, 1),
            periodo_hasta=date(2026, 6, 30),
            soporte=Evidencia.Soporte.DIGITAL,
        )
        FicheroEvidencia.objects.create(
            evidencia=evidencia,
            version=1,
            nombre_original="memoria.pdf",
            nombre_interno="f0f2123d-9f07-4210-a9f4-fce7995b1d38",
            tamano=128,
            tipo_mime="application/pdf",
            sha256="a" * 64,
            vigente=True,
            subido_por=self.usuario,
        )
        otro = FicheroEvidencia(
            evidencia=evidencia,
            version=2,
            nombre_original="memoria-v2.pdf",
            nombre_interno="2eb0ba4b-babe-4a0d-90c6-4ea69471e8e0",
            tamano=140,
            tipo_mime="application/pdf",
            sha256="b" * 64,
            vigente=True,
            subido_por=self.usuario,
        )

        with self.assertRaises(ValidationError):
            otro.full_clean()

        Clasificacion.objects.create(
            evidencia=evidencia,
            criterio=self.criterio,
            clasificada_por=self.usuario,
        )

        self.assertEqual(evidencia.ficheros.count(), 1)
        self.assertEqual(evidencia.clasificaciones.count(), 1)

    def test_evidencia_en_papel_exige_custodia_y_no_admite_archivo(self):
        evidencia = Evidencia(
            ciclo=self.ciclo,
            tipo_evidencia=self.tipo_evidencia,
            titulo="Evidencia en papel",
            descripcion="Documento oficial",
            curso_academico=2025,
            periodo_desde=date(2025, 9, 1),
            periodo_hasta=date(2026, 6, 30),
            soporte=Evidencia.Soporte.PAPEL,
        )

        with self.assertRaises(ValidationError):
            evidencia.full_clean()

        evidencia.custodia_original = "Caja fuerte 1"
        evidencia.full_clean()
        evidencia.save()

        fichero = FicheroEvidencia(
            evidencia=evidencia,
            version=1,
            nombre_original="documento.pdf",
            nombre_interno="9bfdd1fa-e6e5-4e0f-af0f-a5d6d5d766b7",
            tamano=90,
            tipo_mime="application/pdf",
            sha256="c" * 64,
            vigente=True,
            subido_por=self.usuario,
        )

        with self.assertRaises(ValidationError):
            fichero.full_clean()

    def test_ciclo_cerrado_rechaza_evidencia_y_clasificacion(self):
        ciclo_cerrado = Ciclo.objects.create(
            carrera=self.carrera,
            version_normativa=self.version,
            tipo="ordinario",
            anio_base=2027,
            curso_inicial=2022,
            curso_final=2026,
            estado=Ciclo.Estado.CERRADO,
            fecha_apertura=date(2027, 1, 1),
            fecha_cierre=date(2027, 12, 1),
        )

        evidencia = Evidencia(
            ciclo=ciclo_cerrado,
            tipo_evidencia=self.tipo_evidencia,
            titulo="Evidencia fuera de plazo",
            descripcion="No debe permitirse",
            curso_academico=2026,
            periodo_desde=date(2026, 1, 1),
            periodo_hasta=date(2026, 12, 31),
            soporte=Evidencia.Soporte.DIGITAL,
        )

        with self.assertRaises(ValidationError):
            evidencia.full_clean()

        clasificacion = Clasificacion(
            evidencia=Evidencia.objects.create(
                ciclo=self.ciclo,
                tipo_evidencia=self.tipo_evidencia,
                titulo="Evidencia de prueba",
                descripcion="Desc",
                curso_academico=2025,
                periodo_desde=date(2025, 9, 1),
                periodo_hasta=date(2026, 6, 30),
                soporte=Evidencia.Soporte.DIGITAL,
            ),
            criterio=self.criterio,
            clasificada_por=self.usuario,
        )
        clasificacion.evidencia.ciclo = ciclo_cerrado
        with self.assertRaises(ValidationError):
            clasificacion.full_clean()

    def test_clasificacion_rechaza_criterio_de_otra_version(self):
        otra_version = VersionNormativa.objects.create(
            nombre="Otra versión",
            fecha_aprobacion=date(2024, 1, 1),
            fuentes="Fuente",
            activa=True,
        )
        otra_dimension = Dimension.objects.create(
            version=otra_version,
            codigo="2",
            nombre="Otro nivel",
            orden=2,
        )
        otro_indicador = Indicador.objects.create(
            dimension=otra_dimension,
            codigo="I2",
            texto="Indicador ajeno",
        )
        otro_criterio = Criterio.objects.create(
            indicador=otro_indicador,
            codigo="C2",
            codigo_guia="C-2",
            solo_en_guia=False,
            texto="Criterio de otra versión",
            tipo_dato=Criterio.TipoDato.CUALITATIVO,
            valoracion_por_categoria=False,
        )

        clasificacion = Clasificacion(
            evidencia=Evidencia.objects.create(
                ciclo=self.ciclo,
                tipo_evidencia=self.tipo_evidencia,
                titulo="Evidencia",
                descripcion="de prueba",
                curso_academico=2025,
                periodo_desde=date(2025, 1, 1),
                periodo_hasta=date(2025, 12, 31),
                soporte=Evidencia.Soporte.DIGITAL,
            ),
            criterio=otro_criterio,
            clasificada_por=self.usuario,
        )

        with self.assertRaises(ValidationError):
            clasificacion.full_clean()
