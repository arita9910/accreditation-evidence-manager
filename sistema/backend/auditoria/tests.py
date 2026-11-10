from datetime import timedelta
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from ciclos.modelos import Carrera, Facultad
from cuentas.permisos import PermisoSistema, puede

from .middleware import AuditoriaAccesoDenegadoMiddleware
from .modelos import RegistroAuditoria


class RegistroAuditoriaTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            "auditor",
            "clave-segura-123",
            nombre="Auditor",
            apellidos="Prueba",
            email="auditor@example.com",
        )

    def test_crea_registro_con_campos_basicos(self):
        registro = RegistroAuditoria.objects.create(
            usuario=self.usuario,
            accion="ciclo.abrir",
            entidad="Ciclo",
            detalle={"ciclo_id": 1},
            resultado="correcto",
            ip="127.0.0.1",
            contexto={"origen": "servicio"},
        )

        self.assertEqual(registro.accion, "ciclo.abrir")
        self.assertEqual(registro.resultado, "correcto")
        self.assertEqual(registro.entidad, "Ciclo")
        self.assertEqual(registro.ip, "127.0.0.1")

    def test_save_falla_si_intenta_modificar_un_registro_existente(self):
        registro = RegistroAuditoria.objects.create(
            usuario=self.usuario,
            accion="ciclo.cerrar",
            entidad="Ciclo",
            detalle={"estado": "cerrado"},
            resultado="correcto",
        )

        registro.accion = "ciclo.actualizar"
        with self.assertRaises(ValidationError):
            registro.save()

    def test_delete_y_queryset_update_delete_fallan(self):
        registro = RegistroAuditoria.objects.create(
            usuario=self.usuario,
            accion="usuario.crear",
            entidad="Usuario",
            detalle={"nombre": "Ana"},
            resultado="correcto",
        )

        with self.assertRaises(ValidationError):
            registro.delete()

        with self.assertRaises(ValidationError):
            RegistroAuditoria.objects.filter(pk=registro.pk).update(accion="usuario.actualizar")

        with self.assertRaises(ValidationError):
            RegistroAuditoria.objects.filter(pk=registro.pk).delete()

        with self.assertRaises(ValidationError):
            RegistroAuditoria.objects.filter(pk=registro.pk).bulk_update(
                [registro],
                fields=["accion"],
            )


class AuditoriaApiYPermisosTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            "auditor-api",
            "clave-segura-123",
            nombre="Auditor",
            apellidos="Prueba",
            email="auditor-api@example.com",
        )
        self.director = get_user_model().objects.create_user(
            "director-carrera",
            "clave-segura-123",
            nombre="Director",
            apellidos="Carrera",
            email="director@example.com",
        )
        self.facultad = Facultad.objects.create(nombre="Facultad de auditoría")
        self.carrera = Carrera.objects.create(
            facultad=self.facultad,
            nombre="Carrera de auditoría",
            activa=True,
        )
        self.director.rol = "director_carrera"
        self.director.carrera = self.carrera
        self.director.save(update_fields=["rol", "carrera"])
        self.miembro = get_user_model().objects.create_user(
            "miembro-auditoria",
            "clave-segura-123",
            nombre="Miembro",
            apellidos="Auditoría",
            email="miembro@example.com",
        )
        self.miembro.rol = "miembro"
        self.tecnico = get_user_model().objects.create_user(
            "tecnico",
            "clave-segura-123",
            nombre="Técnico",
            apellidos="Admin",
            email="tecnico@example.com",
        )
        self.tecnico.rol = "administrador_tecnico"

        self.director_session = self.client.session
        self.director_session["rol"] = "director_carrera"
        self.director_session["carrera_id"] = self.carrera.pk
        self.director_session.save()

    def test_api_filtra_por_parametros_y_orden_descendente(self):
        ahora = timezone.now()
        RegistroAuditoria.objects.create(
            usuario=self.usuario,
            accion="usuario.crear",
            entidad="Usuario",
            detalle={"carrera_id": self.carrera.pk, "nombre": "Ana"},
            resultado="correcto",
            fecha_hora=ahora - timedelta(hours=2),
        )
        RegistroAuditoria.objects.create(
            usuario=self.usuario,
            accion="ciclo.abrir",
            entidad="Ciclo",
            detalle={"carrera_id": self.carrera.pk, "tipo": "ordinario"},
            resultado="correcto",
            fecha_hora=ahora - timedelta(hours=1),
        )
        RegistroAuditoria.objects.create(
            usuario=self.director,
            accion="ciclo.cerrar",
            entidad="Ciclo",
            detalle={"carrera_id": self.carrera.pk + 99, "tipo": "extraordinario"},
            resultado="denegado",
            fecha_hora=ahora - timedelta(hours=3),
        )

        self.client.force_login(self.director)
        session = self.client.session
        session["rol"] = "director_carrera"
        session["carrera_id"] = self.carrera.pk
        session.save()
        response = self.client.get(
            "/api/auditoria/?usuario=auditor&accion=ciclo&resultado=correcto&desde={}&hasta={}".format(
                (ahora - timedelta(hours=5)).isoformat(),
                (ahora + timedelta(hours=1)).isoformat(),
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["accion"], "ciclo.abrir")

    def test_director_solo_ve_su_carrera(self):
        RegistroAuditoria.objects.create(
            usuario=self.usuario,
            accion="ciclo.abrir",
            entidad="Ciclo",
            detalle={"carrera_id": self.carrera.pk},
            resultado="correcto",
        )
        RegistroAuditoria.objects.create(
            usuario=self.usuario,
            accion="ciclo.cerrar",
            entidad="Ciclo",
            detalle={"carrera_id": self.carrera.pk + 99},
            resultado="correcto",
        )

        self.assertTrue(puede(self.director, "consultar_auditoria", objeto={"carrera_id": self.carrera.pk}))
        self.assertFalse(puede(self.director, "consultar_auditoria", objeto={"carrera_id": self.carrera.pk + 99}))

        self.client.force_login(self.director)
        session = self.client.session
        session["rol"] = "director_carrera"
        session["carrera_id"] = self.carrera.pk
        session.save()
        response = self.client.get("/api/auditoria/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["results"][0]["detalle"]["carrera_id"], self.carrera.pk)

    def test_acceso_denegado_se_registra_con_usuario_accion_y_entidad(self):
        self.assertTrue(puede(self.tecnico, "consultar_auditoria"))
        self.miembro.rol = "miembro"
        self.assertFalse(puede(self.miembro, "consultar_auditoria"))

        with self.assertRaises(PermisoSistema):
            raise PermisoSistema("Sin permiso", accion="consultar_auditoria", entidad="Carrera")

        factory = RequestFactory()
        request = factory.get("/api/auditoria/")
        request.user = self.miembro
        request.session = {}
        request.META["REMOTE_ADDR"] = "127.0.0.1"
        request.accion_denegada = "consultar_auditoria"
        request.entidad_denegada = "Auditoria"

        def vista_fallida(_request):
            raise PermissionDenied("No tiene permiso para consultar la auditoría.")

        middleware = AuditoriaAccesoDenegadoMiddleware(vista_fallida)
        with self.assertRaises(PermissionDenied):
            middleware(request)

        registro = RegistroAuditoria.objects.filter(accion="acceso.denegado").latest("fecha_hora")
        self.assertEqual(registro.usuario.username, self.miembro.username)
        self.assertEqual(registro.resultado, "denegado")
        self.assertEqual(registro.accion, "acceso.denegado")
        self.assertIn("auditoria", registro.entidad.lower())
        self.assertEqual(registro.detalle["accion"], "consultar_auditoria")
