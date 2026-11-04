import hashlib
from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection, models
from django.db.models.deletion import ProtectedError
from django.test import TestCase, override_settings
from django.test import SimpleTestCase
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from . import almacenamiento
from .excepciones import manejador_excepciones
from .modelos import ModeloBase
from .paginacion import PaginacionEstandar
from .serializadores import AtribucionUsuarioMixin


class ModeloTemporal(ModeloBase):
    nombre = models.CharField(max_length=100)

    class Meta:
        app_label = "nucleo"


class ModeloTemporalSerializer(AtribucionUsuarioMixin, serializers.ModelSerializer):
    class Meta:
        model = ModeloTemporal
        fields = "__all__"


class ModeloBaseTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tabla_creada = ModeloTemporal._meta.db_table not in (
            connection.introspection.table_names()
        )
        if cls.tabla_creada:
            with connection.schema_editor() as schema_editor:
                schema_editor.create_model(ModeloTemporal)

    @classmethod
    def tearDownClass(cls):
        if cls.tabla_creada:
            with connection.schema_editor() as schema_editor:
                schema_editor.delete_model(ModeloTemporal)
        super().tearDownClass()

    def crear_usuario(self, username):
        return get_user_model().objects.create_user(
            username=username,
            password="Clave-segura-123!",
            nombre="Nombre",
            apellidos="Apellidos",
            email=f"{username}@example.com",
        )

    def test_campos_automaticos_nulos_y_referencias_protegidas(self):
        objeto = ModeloTemporal.objects.create(nombre="Prueba")
        fecha_creacion = objeto.creado_en
        fecha_modificacion = objeto.modificado_en

        self.assertIsNone(objeto.creado_por)
        self.assertIsNone(objeto.modificado_por)
        self.assertIsNotNone(fecha_creacion)
        self.assertIsNotNone(fecha_modificacion)

        fecha_modificacion_obsoleta = fecha_modificacion - timedelta(seconds=1)
        objeto.modificado_en = fecha_modificacion_obsoleta
        objeto.save()
        objeto.refresh_from_db()

        self.assertEqual(objeto.creado_en, fecha_creacion)
        self.assertNotEqual(objeto.modificado_en, fecha_modificacion_obsoleta)

        usuario = self.crear_usuario("autor-protegido")
        objeto.creado_por = usuario
        objeto.modificado_por = usuario
        objeto.save()
        with self.assertRaises(ProtectedError):
            usuario.delete()

    def test_serializador_asigna_autoria_en_alta_y_actualizacion(self):
        primer_usuario = self.crear_usuario("autor-inicial")
        segundo_usuario = self.crear_usuario("autor-cambio")
        request = APIRequestFactory().post("/")
        request.user = primer_usuario

        serializer = ModeloTemporalSerializer(
            data={"nombre": "Inicial"},
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        objeto = serializer.save()

        self.assertEqual(objeto.creado_por, primer_usuario)
        self.assertEqual(objeto.modificado_por, primer_usuario)

        request = APIRequestFactory().patch("/")
        request.user = segundo_usuario
        serializer = ModeloTemporalSerializer(
            objeto,
            data={"nombre": "Actualizado"},
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        objeto = serializer.save()

        self.assertEqual(objeto.creado_por, primer_usuario)
        self.assertEqual(objeto.modificado_por, segundo_usuario)

    def test_usuario_anonimo_no_asigna_autoria(self):
        request = APIRequestFactory().post("/")
        request.user = AnonymousUser()
        serializer = ModeloTemporalSerializer(
            data={"nombre": "Sin autor"},
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        objeto = serializer.save()

        self.assertIsNone(objeto.creado_por)
        self.assertIsNone(objeto.modificado_por)


class AlmacenamientoTests(TestCase):
    def setUp(self):
        self.directorio_temporal = TemporaryDirectory()
        self.addCleanup(self.directorio_temporal.cleanup)
        configuracion_temporal = override_settings(
            EVIDENCIAS_ROOT=Path(self.directorio_temporal.name)
        )
        configuracion_temporal.enable()
        self.addCleanup(configuracion_temporal.disable)

    def test_guardar_repetido_genera_nombres_unicos_y_huellas(self):
        contenido = b"contenido de evidencia"
        primero = almacenamiento.guardar_fichero(
            SimpleUploadedFile("informe.txt", contenido),
            "ensayos",
        )
        segundo = almacenamiento.guardar_fichero(
            SimpleUploadedFile("informe.txt", contenido),
            "ensayos",
        )

        self.assertNotEqual(primero["nombre_interno"], segundo["nombre_interno"])
        self.assertTrue(primero["nombre_interno"].endswith(".txt"))
        self.assertEqual(primero["tamano"], len(contenido))
        self.assertEqual(
            primero["sha256"],
            hashlib.sha256(contenido).hexdigest(),
        )
        ruta = Path(settings.EVIDENCIAS_ROOT, primero["ruta_relativa"]).resolve()
        self.assertTrue(ruta.is_relative_to(Path(settings.EVIDENCIAS_ROOT).resolve()))
        self.assertFalse(ruta.is_relative_to(Path(settings.STATIC_ROOT).resolve()))
        self.assertFalse(ruta.is_relative_to(Path(settings.MEDIA_ROOT).resolve()))

    def test_rutas_absolutas_y_path_traversal_se_rechazan(self):
        with self.assertRaises(ValueError):
            almacenamiento.guardar_fichero(
                SimpleUploadedFile("evidencia.txt", b"contenido"),
                "../fuera",
            )
        with self.assertRaises(ValueError):
            almacenamiento.abrir_fichero("../fuera/evidencia.txt")
        with self.assertRaises(ValueError):
            almacenamiento.abrir_fichero("C:\\fuera\\evidencia.txt")

    def test_verificar_huella_detecta_cambios_y_borrar_elimina_fichero(self):
        contenido = b"contenido original"
        resultado = almacenamiento.guardar_fichero(
            SimpleUploadedFile("evidencia.txt", contenido),
            "ensayos",
        )

        self.assertTrue(
            almacenamiento.verificar_huella(
                resultado["ruta_relativa"],
                resultado["sha256"],
            )
        )
        ruta = Path(settings.EVIDENCIAS_ROOT, resultado["ruta_relativa"])
        ruta.write_bytes(b"contenido modificado")
        self.assertFalse(
            almacenamiento.verificar_huella(
                resultado["ruta_relativa"],
                resultado["sha256"],
            )
        )
        with almacenamiento.abrir_fichero(resultado["ruta_relativa"]) as archivo:
            self.assertEqual(archivo.read(), b"contenido modificado")
        almacenamiento.borrar_fichero(resultado["ruta_relativa"])
        self.assertFalse(ruta.exists())


class PaginacionTests(SimpleTestCase):
    def test_tamano_de_pagina_es_configurable_en_la_peticion(self):
        request = Request(APIRequestFactory().get("/", {"page_size": "2"}))
        paginador = PaginacionEstandar()
        pagina = paginador.paginate_queryset([1, 2, 3], request)
        respuesta = paginador.get_paginated_response(pagina)

        self.assertEqual(pagina, [1, 2])
        self.assertEqual(respuesta.data["count"], 3)
        self.assertIsNotNone(respuesta.data["next"])


class ManejadorExcepcionesTests(SimpleTestCase):
    def test_error_de_validacion_tiene_formato_comun_en_espanol(self):
        response = manejador_excepciones(
            ValidationError({"nombre": ["Este campo es obligatorio."]}),
            {},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            set(response.data),
            {"codigo", "mensaje", "detalle"},
        )
        self.assertEqual(response.data["codigo"], "invalid")
        self.assertEqual(
            response.data["mensaje"],
            "La solicitud contiene datos no válidos.",
        )
        self.assertIn("nombre", response.data["detalle"])
