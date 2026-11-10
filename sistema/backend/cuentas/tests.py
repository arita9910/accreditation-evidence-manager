from django.core.exceptions import ValidationError
from django.test import TestCase

from ciclos.modelos import Carrera, Facultad
from .modelos import Usuario


class UsuarioTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.facultad = Facultad.objects.create(nombre="Facultad de Ingeniería")
        cls.carrera = Carrera.objects.create(
            facultad=cls.facultad,
            nombre="Ingeniería de Software",
            activa=True,
        )

    def test_create_user_hashes_password_and_is_active(self):
        password = "Clave-segura-123!"
        user = Usuario(
            username="usuario-prueba",
            nombre="Nombre",
            apellidos="Apellidos",
            email="usuario@example.com",
        )
        user.set_password(password)
        user.save()

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

    def test_administrador_tecnico_no_debe_tener_carrera(self):
        user = Usuario(
            username="admin-sin-carrera",
            nombre="Nombre",
            apellidos="Apellidos",
            email="admin@example.com",
            rol=Usuario.Rol.ADMINISTRADOR_TECNICO,
            carrera=self.carrera,
        )
        user.set_password("Clave-segura-123!")

        with self.assertRaises(ValidationError):
            user.full_clean()

    def test_director_de_carrera_debe_tener_carrera(self):
        user = Usuario(
            username="director-sin-carrera",
            nombre="Nombre",
            apellidos="Apellidos",
            email="director@example.com",
            rol=Usuario.Rol.DIRECTOR_CARRERA,
        )
        user.set_password("Clave-segura-123!")

        with self.assertRaises(ValidationError):
            user.full_clean()

        director = Usuario(
            username="director-con-carrera",
            nombre="Nombre",
            apellidos="Apellidos",
            email="director2@example.com",
            rol=Usuario.Rol.DIRECTOR_CARRERA,
            carrera=self.carrera,
        )
        director.set_password("Clave-segura-123!")

        director.full_clean()
