from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from estructura.models import Dimension, VersionNormativa

from .models import AsignacionDimension, Carrera, Ciclo, Facultad
from .servicios import (
    abrir_ciclo,
    asignar_dimension,
    cerrar_ciclo,
    crear_carrera,
    crear_facultad,
    exigir_ciclo_abierto,
    quitar_asignacion,
)


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


class ServiciosCiclosTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            "miembro2",
            "clave-segura-456",
            nombre="Miembro",
            apellidos="Comision",
            email="miembro2@example.com",
        )
        self.facultad = crear_facultad("Ciencias")
        self.carrera = crear_carrera(self.facultad, "Física")
        self.otra_carrera = crear_carrera(self.facultad, "Química")
        self.version = VersionNormativa.objects.create(
            nombre="SEA-CU 2025",
            fecha_aprobacion=date(2025, 1, 1),
            fuentes="Fuente",
            activa=True,
        )
        self.dimension = Dimension.objects.create(
            version=self.version,
            codigo="2",
            nombre="Eficacia",
            orden=2,
        )

    def test_crear_facultad_y_carrera_con_validacion_basica(self):
        facultad = crear_facultad("Medicina")
        carrera = crear_carrera(facultad, "Enfermería")

        self.assertEqual(facultad.nombre, "Medicina")
        self.assertEqual(carrera.nombre, "Enfermería")
        self.assertTrue(carrera.activa)

    def test_abrir_ciclo_valida_reglas_de_negocio(self):
        ciclo = abrir_ciclo(
            self.carrera,
            "ordinario",
            2026,
            2021,
            self.version,
        )

        self.assertEqual(ciclo.estado, Ciclo.Estado.ABIERTO)
        self.assertEqual(ciclo.curso_final, 2025)

        with self.assertRaises(ValidationError):
            abrir_ciclo(
                self.carrera,
                "extraordinario",
                2027,
                2022,
                self.version,
            )

        ciclo_cerrado = Ciclo.objects.create(
            carrera=self.otra_carrera,
            version_normativa=self.version,
            tipo="ordinario",
            anio_base=2025,
            curso_inicial=2020,
            curso_final=2024,
            estado=Ciclo.Estado.CERRADO,
            fecha_cierre=date(2026, 11, 1),
        )
        with self.assertRaises(ValidationError):
            abrir_ciclo(
                self.carrera,
                "extraordinario",
                2028,
                2023,
                self.version,
                ciclo_anterior=ciclo_cerrado,
            )

    def test_cerrar_ciclo_fija_fecha_y_valida_vigencia(self):
        ciclo = abrir_ciclo(
            self.carrera,
            "ordinario",
            2026,
            2021,
            self.version,
        )

        ciclo = cerrar_ciclo(ciclo, categoria_obtenida="Acreditada", vigencia_anios=5)

        self.assertEqual(ciclo.estado, Ciclo.Estado.CERRADO)
        self.assertIsNotNone(ciclo.fecha_cierre)
        self.assertEqual(ciclo.vigencia_anios, 5)
        self.assertEqual(ciclo.categoria_obtenida, "Acreditada")

        ciclo_invalido = abrir_ciclo(
            self.otra_carrera,
            "extraordinario",
            2027,
            2022,
            self.version,
        )
        with self.assertRaises(ValidationError):
            cerrar_ciclo(ciclo_invalido, vigencia_anios=6)

    def test_exigir_ciclo_abierto_y_asignacion_duplicada(self):
        ciclo = abrir_ciclo(
            self.carrera,
            "ordinario",
            2026,
            2021,
            self.version,
        )

        asignacion = asignar_dimension(ciclo, self.usuario, self.dimension)
        self.assertEqual(asignacion.ciclo, ciclo)

        with self.assertRaises(ValidationError):
            asignar_dimension(ciclo, self.usuario, self.dimension)

        self.assertEqual(quitar_asignacion(ciclo, self.usuario, self.dimension), 1)

        ciclo_cerrado = cerrar_ciclo(ciclo, vigencia_anios=7)
        with self.assertRaises(ValidationError):
            exigir_ciclo_abierto(ciclo_cerrado)

        with self.assertRaises(ValidationError):
            asignar_dimension(ciclo_cerrado, self.usuario, self.dimension)
