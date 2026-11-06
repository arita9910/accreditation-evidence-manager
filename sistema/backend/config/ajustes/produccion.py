import os

from django.core.exceptions import ImproperlyConfigured

from .base import *

if CATALOGO_API_DESARROLLO:
    raise ImproperlyConfigured(
        "CATALOGO_API_DESARROLLO no puede habilitarse en producción."
    )


def _required_environment_variable(name):
    value = os.environ.get(name)
    if not value:
        raise ImproperlyConfigured(f"Define la variable de entorno {name}.")
    return value


SECRET_KEY = _required_environment_variable("SECRET_KEY")
DEBUG = False
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("ALLOWED_HOSTS", "").split(",")
    if host.strip()
]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _required_environment_variable("DB_NAME"),
        "USER": _required_environment_variable("DB_USER"),
        "PASSWORD": _required_environment_variable("DB_PASSWORD"),
        "HOST": _required_environment_variable("DB_HOST"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}
