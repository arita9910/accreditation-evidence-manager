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


class CuentaApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.facultad = Facultad.objects.create(nombre="Facultad de Ingeniería")
        cls.carrera = Carrera.objects.create(
            facultad=cls.facultad,
            nombre="Ingeniería de Software",
            activa=True,
        )
        cls.admin = Usuario.objects.create_user(
            username="admin-tek",
            nombre="Admin",
            apellidos="Técnico",
            email="admin@ejemplo.com",
            password="Clave-segura-123!",
            rol=Usuario.Rol.ADMINISTRADOR_TECNICO,
        )
        cls.director = Usuario.objects.create_user(
            username="director-carrera",
            nombre="Director",
            apellidos="Carrera",
            email="director@ejemplo.com",
            password="Clave-segura-123!",
            rol=Usuario.Rol.DIRECTOR_CARRERA,
            carrera=cls.carrera,
        )

    def test_login_y_perfil_autenticado(self):
        response = self.client.post(
            "/api/sesion/",
            {"username": "admin-tek", "password": "Clave-segura-123!"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["usuario"]["username"], "admin-tek")

        response = self.client.get("/api/cuentas/yo/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "admin-tek")

    def test_cambio_clave_y_logout(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            "/api/cuentas/cambiar-clave/",
            {"password_actual": "Clave-segura-123!", "password_nueva": "NuevaClave-456!"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password("NuevaClave-456!"))

        response = self.client.delete("/api/sesion/")
        self.assertEqual(response.status_code, 200)

        profile = self.client.get("/api/cuentas/yo/")
        self.assertEqual(profile.status_code, 403)

    def test_login_fallido_bloquea_posteriores_intentos(self):
        for _ in range(5):
            self.client.post(
                "/api/sesion/",
                {"username": "admin-tek", "password": "password-mala"},
                content_type="application/json",
            )

        response = self.client.post(
            "/api/sesion/",
            {"username": "admin-tek", "password": "password-mala"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 403)

    def test_administrador_tecnico_puede_gestionar_usuarios_y_roles(self):
        self.client.force_login(self.admin)

        response = self.client.get("/api/usuarios/")
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.json()), 2)

        response = self.client.post(
            "/api/usuarios/",
            {
                "username": "nuevo-director",
                "nombre": "Nuevo",
                "apellidos": "Director",
                "email": "nuevo@ejemplo.com",
                "password": "Clave-segura-456!",
                "rol": Usuario.Rol.DIRECTOR_CARRERA,
                "carrera": self.carrera.pk,
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        usuario_creado = response.json()
        self.assertEqual(usuario_creado["username"], "nuevo-director")

        role_response = self.client.post(
            f"/api/usuarios/{usuario_creado['id']}/roles/",
            {"rol": Usuario.Rol.ADMINISTRADOR_TECNICO},
            content_type="application/json",
        )
        self.assertEqual(role_response.status_code, 200)
        self.assertEqual(role_response.json()["rol"], Usuario.Rol.ADMINISTRADOR_TECNICO)

        delete_response = self.client.delete(f"/api/usuarios/{usuario_creado['id']}/roles/")
        self.assertEqual(delete_response.status_code, 200)
        self.assertEqual(delete_response.json()["rol"], Usuario.Rol.ADMINISTRADOR_TECNICO)
