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


EVIDENCIAS_ROOT = _configured_path(
    "EVIDENCIAS_ROOT",
    BASE_DIR.parent / "almacen" / "evidencias",
)
if (
    EVIDENCIAS_ROOT == STATIC_ROOT.resolve()
    or STATIC_ROOT.resolve() in EVIDENCIAS_ROOT.parents
):
    raise ImproperlyConfigured("EVIDENCIAS_ROOT debe estar fuera de STATIC_ROOT.")
MEDIA_ROOT = EVIDENCIAS_ROOT

LOG_DIR = _configured_path("LOG_DIR", BASE_DIR / "logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

SECRET_KEY = "development-only-not-for-production"
DEBUG = False
ALLOWED_HOSTS = []

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
