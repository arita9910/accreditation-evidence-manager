import importlib
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.conf import settings
from django.test import SimpleTestCase

from .ajustes import base


class RuntimeConfigurationTests(SimpleTestCase):
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
        self.assertEqual(settings.MEDIA_ROOT, settings.EVIDENCIAS_ROOT)
        self.assertFalse(
            settings.EVIDENCIAS_ROOT.is_relative_to(settings.STATIC_ROOT)
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
