import importlib
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.conf import settings
from django.test import SimpleTestCase, override_settings
from django.urls import Resolver404, clear_url_caches, resolve

from .ajustes import base


class RuntimeConfigurationTests(SimpleTestCase):
    def test_health_endpoint_is_public_and_returns_ok(self):
        response = self.client.get("/api/salud/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"estado": "ok"})

    def test_openapi_schema_is_available_only_in_development(self):
        from . import urls

        try:
            with override_settings(DEBUG=True):
                importlib.reload(urls)
                clear_url_caches()
                response = self.client.get("/api/esquema/?format=json")
                self.assertEqual(response.status_code, 200)
                self.assertIn("application/vnd.oai.openapi", response["Content-Type"])
                self.assertEqual(resolve("/api/esquema/").url_name, "schema")
                self.assertIn(
                    "/api/salud/",
                    json.loads(response.content)["paths"],
                )

            with override_settings(DEBUG=False):
                importlib.reload(urls)
                clear_url_caches()
                with self.assertRaises(Resolver404):
                    resolve("/api/esquema/")
        finally:
            importlib.reload(urls)
            clear_url_caches()

    def test_development_uses_sqlite(self):
        development = importlib.import_module("config.ajustes.desarrollo")

        self.assertEqual(
            development.DATABASES["default"]["ENGINE"],
            "django.db.backends.sqlite3",
        )

    def test_production_uses_postgresql_environment_values(self):
        environment = {
            "SECRET_KEY": "test-only-secret-key",
            "ALLOWED_HOSTS": "example.test, localhost",
            "DB_NAME": "sea_cu",
            "DB_USER": "sea_cu_user",
            "DB_PASSWORD": "test-only-password",
            "DB_HOST": "db.example.test",
            "DB_PORT": "5433",
        }
        with patch.dict(os.environ, environment):
            production = importlib.import_module("config.ajustes.produccion")

        self.assertFalse(production.DEBUG)
        self.assertEqual(
            production.DATABASES["default"]["ENGINE"],
            "django.db.backends.postgresql",
        )
        self.assertEqual(production.DATABASES["default"]["NAME"], "sea_cu")
        self.assertEqual(production.DATABASES["default"]["PORT"], "5433")
        self.assertEqual(production.ALLOWED_HOSTS, ["example.test", "localhost"])

    def test_error_logs_rotate(self):
        configured_handler = settings.LOGGING["handlers"]["archivo_errores"]
        self.assertEqual(
            configured_handler["class"],
            "logging.handlers.RotatingFileHandler",
        )
        self.assertGreater(configured_handler["maxBytes"], 0)
        self.assertGreater(configured_handler["backupCount"], 0)

        with TemporaryDirectory() as temporary_directory:
            log_path = Path(temporary_directory) / "errores.log"
            handler = RotatingFileHandler(
                log_path,
                maxBytes=16,
                backupCount=2,
                encoding="utf-8",
            )
            logger = logging.getLogger("config.tests.rotation")
            logger.addHandler(handler)
            logger.setLevel(logging.ERROR)
            try:
                logger.error("primer mensaje de prueba")
                logger.error("segundo mensaje de prueba")
            finally:
                logger.removeHandler(handler)
                handler.close()

            self.assertTrue(Path(f"{log_path}.1").exists())

    def test_evidence_storage_is_private_and_configurable(self):
        self.assertNotEqual(settings.MEDIA_ROOT, settings.EVIDENCIAS_ROOT)
        self.assertFalse(
            settings.EVIDENCIAS_ROOT.is_relative_to(settings.MEDIA_ROOT)
            or settings.MEDIA_ROOT.is_relative_to(settings.EVIDENCIAS_ROOT)
        )
        self.assertFalse(
            settings.EVIDENCIAS_ROOT.is_relative_to(settings.STATIC_ROOT)
            or settings.STATIC_ROOT.is_relative_to(settings.EVIDENCIAS_ROOT)
        )
        with patch.dict(os.environ, {"EVIDENCIAS_ROOT": "private-evidence"}):
            configured_path = base._configured_path(
                "EVIDENCIAS_ROOT",
                base.BASE_DIR.parent / "almacen" / "evidencias",
            )

        self.assertEqual(
            configured_path,
            (base.BASE_DIR / "private-evidence").resolve(),
        )
