from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from auditoria.servicios import obtener_registros
from ciclos.modelos import Carrera, Ciclo, Facultad
from cuentas.permisos import puede
from estructura.models import Dimension, VersionNormativa
from valoracion.models import Valoracion

from .models import AccionMejora, PlanMejora
from .servicios import crear_accion_mejora, crear_plan_mejora, registrar_seguimiento, vincular_evidencia


class MejoraModelosYServiciosTests(TestCase):
    def setUp(self):
        self.Usuario = get_user_model()
        self.facultad = Facultad.objects.create(nombre="Ingeniería")
        self.carrera = Carrera.objects.create(facultad=self.facultad, nombre="Informática")
        self.otra_carrera = Carrera.objects.create(facultad=self.facultad, nombre="Industrial")
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
        self.ciclo = Ciclo.objects.create(
            carrera=self.carrera,
            version_normativa=self.version,
            tipo="ordinario",
            anio_base=2026,
            curso_inicial=2021,
            curso_final=2025,
            estado=Ciclo.Estado.ABIERTO,
        )
        self.director = self.Usuario.objects.create_user(
            "director_mejora",
            "clave-segura-123",
            nombre="Director",
            apellidos="Carrera",
            email="director@example.com",
            rol=self.Usuario.Rol.DIRECTOR_CARRERA,
            carrera=self.carrera,
        )
        self.miembro = self.Usuario.objects.create_user(
            "miembro_mejora",
            "clave-segura-456",
            nombre="Miembro",
            apellidos="Carrera",
            email="miembro@example.com",
            rol=self.Usuario.Rol.DIRECTOR_CARRERA,
            carrera=self.otra_carrera,
        )
        self.debilidad = Valoracion.objects.create(
            ciclo=self.ciclo,
            dimension=self.dimension,
            tipo=Valoracion.Tipo.DEBILIDAD,
            texto="La dimensión no está bien definida.",
            redactada_por=self.director,
        )
        self.plan = crear_plan_mejora(self.ciclo, usuario=self.director)

    def test_plan_mejora_se_crea_con_ciclo_abierto_y_auditoria(self):
        self.assertEqual(self.plan.ciclo_id, self.ciclo.pk)
        self.assertTrue(puede(self.director, "crear_plan_mejora", objeto=self.ciclo))
        self.assertFalse(puede(self.miembro, "crear_plan_mejora", objeto=self.ciclo))
        registros = obtener_registros()
        self.assertTrue(any(registro["accion"] == "crear_plan_mejora" for registro in registros))

    def test_accion_de_mejora_exige_debilidad_y_mismo_ciclo(self):
        accion = crear_accion_mejora(
            self.plan,
            self.debilidad,
            "Definir mejor los criterios del plan.",
            self.director,
            date.today() + timedelta(days=10),
            usuario=self.director,
        )

        self.assertEqual(accion.debilidad_id, self.debilidad.pk)
        self.assertEqual(accion.plan_id, self.plan.pk)

        self.debilidad.tipo = Valoracion.Tipo.FORTALEZA
        self.debilidad.save()
        with self.assertRaises(ValidationError):
            AccionMejora(
                plan=self.plan,
                debilidad=self.debilidad,
                descripcion="Se intenta crear una acción sin regla de negocio.",
                responsable=self.director,
                fecha_limite=date.today() + timedelta(days=3),
            ).full_clean()

    def test_ciclo_cerrado_rechaza_plan_y_seguimiento(self):
        with self.assertRaises(ValidationError):
            crear_plan_mejora(self.ciclo, usuario=self.director)

        accion = crear_accion_mejora(
            self.plan,
            self.debilidad,
            "Revisar y cerrar la debilidad.",
            self.director,
            date.today() + timedelta(days=30),
            usuario=self.director,
        )

        self.ciclo.estado = Ciclo.Estado.CERRADO
        self.ciclo.fecha_cierre = date(2026, 12, 1)
        self.ciclo.save()

        with self.assertRaises(ValidationError):
            registrar_seguimiento(accion, 50, "Se recoge el avance.", usuario=self.director)

    def test_vincular_evidencia_requiere_mismo_ciclo(self):
        with self.assertRaises(ValidationError):
            vincular_evidencia(
                self.plan.acciones.first(),
                None,
                usuario=self.director,
            )
