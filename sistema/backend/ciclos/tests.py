from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from estructura.models import Dimension, VersionNormativa

from .models import AsignacionDimension, Carrera, Ciclo, Facultad


class ModelosCiclosTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            "miembro",
            "clave-segura-123",
            nombre="Miembro",
            apellidos="Comision",
            email="miembro@example.com",
        )
        self.facultad = Facultad.objects.create(nombre="Ingeniería")
        self.carrera = Carrera.objects.create(
            facultad=self.facultad,
            nombre="Ingeniería Informática",
            activa=True,
        )
        self.otra_carrera = Carrera.objects.create(
            facultad=self.facultad,
            nombre="Ingeniería Industrial",
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

    def crear_ciclo(self, carrera, **kwargs):
        datos = {
            "carrera": carrera,
            "version_normativa": self.version,
            "tipo": "ordinario",
            "anio_base": 2026,
            "curso_inicial": 2021,
            "curso_final": 2025,
            "estado": Ciclo.Estado.ABIERTO,
        }
        datos.update(kwargs)
        return Ciclo.objects.create(**datos)

    def test_apertura_crea_ciclo_abierto_valido(self):
        ciclo = self.crear_ciclo(self.carrera)

        self.assertEqual(ciclo.estado, Ciclo.Estado.ABIERTO)
        self.assertIsNotNone(ciclo.fecha_apertura)
        self.assertIsNone(ciclo.fecha_cierre)

    def test_no_permite_dos_ciclos_abiertos_en_una_carrera(self):
        self.crear_ciclo(self.carrera)

        with self.assertRaises(ValidationError):
            self.crear_ciclo(self.carrera, tipo="extraordinario", anio_base=2027)

    def test_valida_que_ciclo_anterior_sea_de_la_misma_carrera(self):
        ciclo_otra_carrera = self.crear_ciclo(
            self.otra_carrera,
            estado=Ciclo.Estado.CERRADO,
            fecha_cierre=date(2026, 11, 1),
        )
        ciclo = Ciclo(
            carrera=self.carrera,
            version_normativa=self.version,
            tipo="ordinario",
            anio_base=2027,
            curso_inicial=2022,
            curso_final=2026,
            ciclo_anterior=ciclo_otra_carrera,
        )

        with self.assertRaises(ValidationError):
            ciclo.full_clean()

    def test_ciclo_cerrado_queda_en_solo_lectura(self):
        ciclo = self.crear_ciclo(self.carrera)
        ciclo.estado = Ciclo.Estado.CERRADO
        ciclo.fecha_cierre = date(2026, 12, 1)
        ciclo.save()

        ciclo.tipo = "actualizado"
        with self.assertRaises(ValidationError):
            ciclo.save()

    def test_vigencia_valida_y_rechaza_valor_incorrecto(self):
        ciclo = self.crear_ciclo(self.carrera)
        ciclo.estado = Ciclo.Estado.CERRADO
        ciclo.fecha_cierre = date(2026, 12, 1)
        ciclo.vigencia_anios = 5
        ciclo.save()

        ciclo_invalido = self.crear_ciclo(
            self.otra_carrera,
            anio_base=2028,
            curso_inicial=2023,
            curso_final=2027,
        )
        ciclo_invalido.estado = Ciclo.Estado.CERRADO
        ciclo_invalido.fecha_cierre = date(2027, 12, 1)
        ciclo_invalido.vigencia_anios = 6

        with self.assertRaises(ValidationError):
            ciclo_invalido.save()

    def test_asignacion_duplicada_falla_por_unicidad(self):
        ciclo = self.crear_ciclo(self.carrera)
        AsignacionDimension.objects.create(
            ciclo=ciclo,
            usuario=self.usuario,
            dimension=self.dimension,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            AsignacionDimension.objects.create(
                ciclo=ciclo,
                usuario=self.usuario,
                dimension=self.dimension,
            )
