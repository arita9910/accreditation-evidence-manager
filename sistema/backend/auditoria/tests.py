from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

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
