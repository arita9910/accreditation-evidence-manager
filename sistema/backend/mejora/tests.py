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


class MejoraApiTests(TestCase):
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
            "director_mejora_api",
            "clave-segura-123",
            nombre="Director",
            apellidos="Carrera",
            email="director_api@example.com",
            rol=self.Usuario.Rol.DIRECTOR_CARRERA,
            carrera=self.carrera,
        )
        self.miembro = self.Usuario.objects.create_user(
            "miembro_mejora_api",
            "clave-segura-456",
            nombre="Miembro",
            apellidos="Carrera",
            email="miembro_api@example.com",
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
        self.accion = crear_accion_mejora(
            self.plan,
            self.debilidad,
            "Definir el plan de mejora.",
            self.director,
            date.today() + timedelta(days=10),
            usuario=self.director,
        )

    def test_plan_y_acciones_requieren_permiso_de_director(self):
        self.client.force_login(self.director)
        respuesta = self.client.get(f"/api/ciclos/{self.ciclo.pk}/plan/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("id", respuesta.json())

        payload = {
            "debilidad": self.debilidad.pk,
            "descripcion": "Revisar la debilidad del ciclo.",
            "responsable": self.director.pk,
            "fecha_limite": (date.today() + timedelta(days=15)).isoformat(),
        }
        respuesta = self.client.post(
            f"/api/planes/{self.plan.pk}/acciones/",
            payload,
            content_type="application/json",
        )
        self.assertEqual(respuesta.status_code, 201)

        self.client.force_login(self.miembro)
        respuesta = self.client.get(f"/api/ciclos/{self.ciclo.pk}/plan/")
        self.assertEqual(respuesta.status_code, 403)

        respuesta = self.client.post(
            f"/api/planes/{self.plan.pk}/acciones/",
            payload,
            content_type="application/json",
        )
        self.assertEqual(respuesta.status_code, 403)

    def test_api_permite_seguimiento_y_plan_anterior(self):
        self.client.force_login(self.director)
        respuesta = self.client.post(
            f"/api/acciones/{self.accion.pk}/seguimientos/",
            {"avance": 30, "nota": "Se inició el seguimiento."},
            content_type="application/json",
        )
        self.assertEqual(respuesta.status_code, 201)

        ciclo_anterior = Ciclo.objects.create(
            carrera=self.carrera,
            version_normativa=self.version,
            tipo="ordinario",
            anio_base=2025,
            curso_inicial=2020,
            curso_final=2024,
            estado=Ciclo.Estado.CERRADO,
            fecha_cierre=date(2026, 6, 30),
        )
        debilidad_anterior = Valoracion(
            ciclo=ciclo_anterior,
            dimension=self.dimension,
            tipo=Valoracion.Tipo.DEBILIDAD,
            texto="Debilidad del ciclo anterior.",
            redactada_por=self.director,
        )
        Valoracion.objects.bulk_create([debilidad_anterior])
        plan_anterior = PlanMejora(
            ciclo=ciclo_anterior,
            estado=PlanMejora.Estado.CERRADO,
            aprobado_por=self.director,
        )
        PlanMejora.objects.bulk_create([plan_anterior])
        accion_anterior = AccionMejora(
            plan=plan_anterior,
            debilidad=debilidad_anterior,
            descripcion="Acción anterior.",
            responsable=self.director,
            fecha_limite=date.today() + timedelta(days=5),
            estado=AccionMejora.Estado.CUMPLIDA,
            valoracion_resultado="Cumplida",
        )
        AccionMejora.objects.bulk_create([accion_anterior])

        self.ciclo.ciclo_anterior = ciclo_anterior
        self.ciclo.save()

        respuesta = self.client.get(f"/api/ciclos/{self.ciclo.pk}/plan-anterior/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("plan", respuesta.json())
        self.assertIn("acciones", respuesta.json())
