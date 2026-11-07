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


class ApiCiclosTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            "api-miembro",
            "clave-segura-789",
            nombre="Miembro",
            apellidos="API",
            email="api-miembro@example.com",
        )
        self.facultad = Facultad.objects.create(nombre="Tecnologías")
        self.carrera = Carrera.objects.create(
            facultad=self.facultad,
            nombre="Ingeniería de Software",
            activa=True,
        )
        self.version = VersionNormativa.objects.create(
            nombre="SEA-CU 2026",
            fecha_aprobacion=date(2026, 1, 1),
            fuentes="Fuente API",
            activa=True,
        )
        self.dimension = Dimension.objects.create(
            version=self.version,
            codigo="3",
            nombre="Impacto",
            orden=3,
        )

    def test_facultades_get_y_post(self):
        respuesta_get = self.client.get("/api/facultades/")
        self.assertEqual(respuesta_get.status_code, 200)
        datos_get = respuesta_get.json()
        self.assertIn("results", datos_get)
        self.assertIn("count", datos_get)

        respuesta_post = self.client.post(
            "/api/facultades/",
            data={"nombre": "Ciencias Sociales"},
            content_type="application/json",
        )
        self.assertEqual(respuesta_post.status_code, 201)
        self.assertEqual(respuesta_post.json()["nombre"], "Ciencias Sociales")

    def test_carreras_get_post_y_patch(self):
        respuesta_post = self.client.post(
            "/api/carreras/",
            data={
                "facultad": self.facultad.pk,
                "nombre": "Ciencia de Datos",
                "activa": True,
            },
            content_type="application/json",
        )
        self.assertEqual(respuesta_post.status_code, 201)
        carrera_id = respuesta_post.json()["id"]

        respuesta_get = self.client.get("/api/carreras/")
        self.assertEqual(respuesta_get.status_code, 200)
        self.assertIn("results", respuesta_get.json())

        respuesta_patch = self.client.patch(
            f"/api/carreras/{carrera_id}/",
            data={"activa": False},
            content_type="application/json",
        )
        self.assertEqual(respuesta_patch.status_code, 200)
        self.assertFalse(respuesta_patch.json()["activa"])

    def test_ciclos_endpoints_y_filtros(self):
        respuesta_apertura = self.client.post(
            "/api/ciclos/",
            data={
                "carrera": self.carrera.pk,
                "version_normativa": self.version.pk,
                "tipo": "ordinario",
                "anio_base": 2026,
                "curso_inicial": 2021,
            },
            content_type="application/json",
        )
        self.assertEqual(respuesta_apertura.status_code, 201)
        ciclo_id = respuesta_apertura.json()["id"]

        respuesta_lista = self.client.get(f"/api/ciclos/?carrera={self.carrera.pk}&estado=abierto")
        self.assertEqual(respuesta_lista.status_code, 200)
        self.assertEqual(respuesta_lista.json()["count"], 1)

        respuesta_detalle = self.client.get(f"/api/ciclos/{ciclo_id}/")
        self.assertEqual(respuesta_detalle.status_code, 200)
        self.assertEqual(respuesta_detalle.json()["estado"], "abierto")

        respuesta_cierre = self.client.post(
            f"/api/ciclos/{ciclo_id}/cerrar/",
            data={"categoria_obtenida": "Acreditada", "vigencia_anios": 7},
            content_type="application/json",
        )
        self.assertEqual(respuesta_cierre.status_code, 200)
        self.assertEqual(respuesta_cierre.json()["estado"], "cerrado")

    def test_asignaciones_get_post_delete(self):
        ciclo = abrir_ciclo(
            self.carrera,
            "ordinario",
            2026,
            2021,
            self.version,
        )
        respuesta_post = self.client.post(
            f"/api/ciclos/{ciclo.pk}/asignaciones/",
            data={"usuario": self.usuario.pk, "dimension": self.dimension.pk},
            content_type="application/json",
        )
        self.assertEqual(respuesta_post.status_code, 201)

        respuesta_get = self.client.get(f"/api/ciclos/{ciclo.pk}/asignaciones/")
        self.assertEqual(respuesta_get.status_code, 200)
        self.assertEqual(respuesta_get.json()["count"], 1)

        respuesta_delete = self.client.delete(
            f"/api/ciclos/{ciclo.pk}/asignaciones/",
            data={"usuario": self.usuario.pk, "dimension": self.dimension.pk},
            content_type="application/json",
        )
        self.assertEqual(respuesta_delete.status_code, 204)

    def test_errores_estandar_en_espanol(self):
        respuesta_invalida = self.client.post(
            "/api/ciclos/",
            data={
                "carrera": self.carrera.pk,
                "version_normativa": self.version.pk,
                "tipo": "ordinario",
                "anio_base": 2026,
            },
            content_type="application/json",
        )
        self.assertEqual(respuesta_invalida.status_code, 400)
        self.assertEqual(respuesta_invalida.json()["codigo"], "invalid")
        self.assertEqual(
            respuesta_invalida.json()["mensaje"],
            "La solicitud contiene datos no válidos.",
        )

        respuesta_no_encontrada = self.client.get("/api/ciclos/999999/")
        self.assertEqual(respuesta_no_encontrada.status_code, 404)
        self.assertEqual(respuesta_no_encontrada.json()["codigo"], "not_found")
