from __future__ import annotations

import json

from django.contrib.auth import get_user_model
from django.db import connection

from .modelos import RegistroAuditoria


def _serializar_json(valor):
    if valor is None:
        return {}
    if isinstance(valor, (dict, list, str, int, float, bool)):
        return valor
    try:
        return json.loads(json.dumps(valor, default=str))
    except TypeError:
        return str(valor)


def registrar(accion, *, usuario=None, entidad=None, detalle=None, contexto=None, **kwargs):
    detalle_serializado = _serializar_json(detalle)
    contexto_serializado = _serializar_json(contexto)
    resultado = kwargs.get("resultado", "correcto")
    ip = kwargs.get("ip")
    usuario_evento = getattr(usuario, "username", None) or getattr(usuario, "user", None) or usuario
    usuario_db = usuario if isinstance(usuario, get_user_model()) else None

    registro = RegistroAuditoria.objects.create(
        usuario=usuario_db,
        accion=accion,
        entidad=entidad,
        detalle=detalle_serializado,
        resultado=resultado,
        ip=ip,
        contexto=contexto_serializado,
    )

    evento = {
        "accion": registro.accion,
        "usuario": usuario_evento,
        "entidad": registro.entidad,
        "detalle": registro.detalle,
        "contexto": registro.contexto,
        "timestamp": registro.fecha_hora.isoformat(),
        "metadatos": dict(kwargs),
    }
    return evento


def obtener_registros():
    registros = []
    for registro in RegistroAuditoria.objects.order_by("-fecha_hora"):
        registros.append(
            {
                "accion": registro.accion,
                "usuario": getattr(registro.usuario, "username", None) or getattr(registro.usuario, "user", None) or registro.usuario,
                "entidad": registro.entidad,
                "detalle": registro.detalle,
                "contexto": registro.contexto,
                "timestamp": registro.fecha_hora.isoformat(),
                "metadatos": {
                    "resultado": registro.resultado,
                    "ip": registro.ip,
                },
            }
        )
    return registros


def limpiar_registros():
    with connection.cursor() as cursor:
        cursor.execute(f"DELETE FROM {RegistroAuditoria._meta.db_table}")


__all__ = ["registrar", "obtener_registros", "limpiar_registros"]
