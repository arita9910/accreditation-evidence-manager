from __future__ import annotations

import threading
from datetime import datetime, timezone


_REGISTROS = []
_REGISTROS_LOCK = threading.Lock()


def registrar(accion, *, usuario=None, entidad=None, detalle=None, contexto=None, **kwargs):
    evento = {
        "accion": accion,
        "usuario": getattr(usuario, "username", None) or getattr(usuario, "user", None) or usuario,
        "entidad": entidad,
        "detalle": detalle,
        "contexto": contexto,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metadatos": kwargs,
    }
    with _REGISTROS_LOCK:
        _REGISTROS.append(evento)
    return evento


def obtener_registros():
    with _REGISTROS_LOCK:
        return list(_REGISTROS)


def limpiar_registros():
    with _REGISTROS_LOCK:
        _REGISTROS.clear()


__all__ = ["registrar", "obtener_registros", "limpiar_registros"]
