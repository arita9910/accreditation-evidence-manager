from django.test import TestCase

from .models import Usuario


class UsuarioTests(TestCase):
    def test_create_user_hashes_password_and_is_active(self):
        password = "Clave-segura-123!"
        user = Usuario.objects.create_user(
            username="usuario-prueba",
            password=password,
            nombre="Nombre",
            apellidos="Apellidos",
            email="usuario@example.com",
        )

        self.assertNotEqual(user.password, password)
        self.assertTrue(user.check_password(password))
        self.assertTrue(user.is_active)

    def test_is_active_tracks_activo(self):
        user = Usuario(
            username="usuario-inactivo",
            nombre="Nombre",
            apellidos="Apellidos",
            email="inactivo@example.com",
            activo=False,
        )

        self.assertFalse(user.is_active)
        user.is_active = True
        self.assertTrue(user.activo)
