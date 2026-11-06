import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parents[2]
STATIC_ROOT = BASE_DIR / "staticfiles"


def _configured_path(environment_variable, default):
    value = os.environ.get(environment_variable)
    path = Path(value).expanduser() if value else default
    if not path.is_absolute():
        path = BASE_DIR / path
    return path.resolve()


def _paths_overlap(first, second):
    return first == second or first in second.parents or second in first.parents


def _configured_boolean(environment_variable, default=False):
    value = os.environ.get(environment_variable)
    if value is None:
        return default
    normalized = value.strip().casefold()
    if normalized in {"1", "true", "yes", "sí", "si"}:
        return True
    if normalized in {"0", "false", "no"}:
        return False
    raise ImproperlyConfigured(
        f"La variable de entorno {environment_variable} debe ser booleana."
    )


EVIDENCIAS_ROOT = _configured_path(
    "EVIDENCIAS_ROOT",
    BASE_DIR.parent / "almacen" / "evidencias",
)
MEDIA_ROOT = _configured_path("MEDIA_ROOT", BASE_DIR / "media")
if _paths_overlap(EVIDENCIAS_ROOT, STATIC_ROOT.resolve()):
    raise ImproperlyConfigured("EVIDENCIAS_ROOT debe estar fuera de STATIC_ROOT.")
if _paths_overlap(EVIDENCIAS_ROOT, MEDIA_ROOT):
    raise ImproperlyConfigured("EVIDENCIAS_ROOT debe estar separado de MEDIA_ROOT.")

LOG_DIR = _configured_path("LOG_DIR", BASE_DIR / "logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

SECRET_KEY = "development-only-not-for-production"
DEBUG = False
ALLOWED_HOSTS = []
CATALOGO_API_DESARROLLO = _configured_boolean("CATALOGO_API_DESARROLLO")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "nucleo.apps.NucleoConfig",
    "estructura.apps.EstructuraConfig",
    "ciclos.apps.CiclosConfig",
    "cuentas.apps.CuentasConfig",
    "auditoria.apps.AuditoriaConfig",
    "evidencias.apps.EvidenciasConfig",
    "valoracion.apps.ValoracionConfig",
    "cuantitativos.apps.CuantitativosConfig",
    "mejora.apps.MejoraConfig",
    "analisis.apps.AnalisisConfig",
    "informes.apps.InformesConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {}
AUTH_USER_MODEL = "cuentas.Usuario"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "nucleo.paginacion.PaginacionEstandar",
    "EXCEPTION_HANDLER": "nucleo.excepciones.manejador_excepciones",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Acreditación Evidencia Manager",
    "DESCRIPTION": "API del sistema de acreditación",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

LANGUAGE_CODE = "es"
TIME_ZONE = "America/Havana"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "errores": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        }
    },
    "handlers": {
        "archivo_errores": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "errores.log"),
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8",
            "formatter": "errores",
            "level": "ERROR",
        }
    },
    "root": {
        "handlers": ["archivo_errores"],
        "level": "ERROR",
    },
}
