from __future__ import annotations

from collections.abc import Iterable

from rest_framework.exceptions import PermissionDenied


class PermisoSistema(PermissionDenied):
    def __init__(
        self,
        detalle="No tiene permiso para realizar esta acción.",
        *,
        accion=None,
        entidad=None,
        **kwargs,
    ):
        super().__init__(detalle, **kwargs)
        self.accion = accion
        self.entidad = entidad


_PERMISOS_POR_ACCION = {
    "crear_facultad": {"administrador_tecnico"},
    "crear_carrera": {"administrador_tecnico"},
    "abrir_ciclo": {"director_carrera", "administrador_tecnico"},
    "cerrar_ciclo": {"director_carrera", "administrador_tecnico"},
    "asignar_dimension": {"director_carrera", "administrador_tecnico"},
    "quitar_asignacion": {"director_carrera", "administrador_tecnico"},
    "listar_facultades": {"administrador_tecnico", "director_carrera"},
    "listar_carreras": {"administrador_tecnico", "director_carrera"},
    "consultar_auditoria": {"administrador_tecnico", "director_carrera"},
    "listar_auditoria": {"administrador_tecnico", "director_carrera"},
}


def _normalizar_token(valor):
    if valor is None:
        return ""
    if isinstance(valor, str):
        texto = valor.strip().lower().replace("-", "_").replace(" ", "_")
        return texto.replace(".", "_")
    return str(valor).strip().lower().replace("-", "_").replace(" ", "_")


def _coerce_carrera_id(valor):
    if valor is None:
        return None

    if isinstance(valor, dict):
        for clave in ("carrera_id", "carrera", "carrera_pk", "id"):
            if clave in valor:
                return _coerce_carrera_id(valor[clave])
        return None

    if hasattr(valor, "pk") and getattr(getattr(valor, "_meta", None), "model_name", None) == "carrera":
        return _coerce_carrera_id(valor.pk)

    for nombre in ("carrera_id", "carrera_pk"):
        try:
            atributo = getattr(valor, nombre, None)
        except Exception:
            atributo = None
        if atributo is not None:
            carrera_id = _coerce_carrera_id(atributo)
            if carrera_id is not None:
                return carrera_id

    for nombre in ("carrera",):
        try:
            atributo = getattr(valor, nombre, None)
        except Exception:
            atributo = None
        if atributo is not None:
            carrera_id = _coerce_carrera_id(atributo)
            if carrera_id is not None:
                return carrera_id

    if isinstance(valor, str):
        valor = valor.strip()
        if valor.isdigit():
            return int(valor)
        return None

    if isinstance(valor, int):
        return valor

    return None


def _ids_carrera_del_usuario(actor):
    if actor is None:
        return set()

    valores = []
    carrera_id = getattr(actor, "carrera_id", None)
    if carrera_id is not None:
        valores.append(carrera_id)

    for nombre in ("carrera_actual", "carrera_pk"):
        try:
            valor = getattr(actor, nombre, None)
        except Exception:
            valor = None
        if valor is not None:
            valores.append(valor)

    try:
        carrera = getattr(actor, "carrera", None)
    except Exception:
        carrera = None
    if carrera is not None:
        valores.append(carrera)

    for nombre in ("carreras", "carreras_asignadas", "carreras_director"):
        try:
            coleccion = getattr(actor, nombre, None)
        except Exception:
            coleccion = None
        if coleccion is None:
            continue
        if hasattr(coleccion, "all"):
            coleccion = coleccion.all()
        if isinstance(coleccion, Iterable) and not isinstance(coleccion, (str, bytes, bytearray, dict)):
            valores.extend(coleccion)

    ids = set()
    for valor in valores:
        carrera_id = _coerce_carrera_id(valor)
        if carrera_id is not None:
            ids.add(carrera_id)
    return ids


def _iterar_roles(actor):
    if actor is None:
        return []

    for nombre in ("rol", "role", "perfil", "perfil_rol", "roles", "grupos"):
        valor = getattr(actor, nombre, None)
        if isinstance(valor, str):
            yield _normalizar_token(valor)
        elif isinstance(valor, Iterable) and not isinstance(valor, (bytes, bytearray, dict)):
            for item in valor:
                yield _normalizar_token(item)

    permisos = getattr(actor, "permisos", None)
    if isinstance(permisos, dict):
        for nombre in permisos:
            yield _normalizar_token(nombre)
    elif isinstance(permisos, Iterable) and not isinstance(permisos, (bytes, bytearray, dict)):
        for item in permisos:
            yield _normalizar_token(item)

    if getattr(actor, "is_superuser", False) or getattr(actor, "is_staff", False):
        yield "administrador_tecnico"
    if getattr(actor, "es_director", False) or getattr(actor, "es_director_carrera", False):
        yield "director_carrera"
    if getattr(actor, "es_administrador_tecnico", False):
        yield "administrador_tecnico"


def _puede_por_contexto(actor, accion, objeto):
    if actor is None or objeto is None:
        return False

    roles = set(_iterar_roles(actor))
    if "administrador_tecnico" in roles:
        return True
    if "director_carrera" not in roles:
        return False

    if isinstance(objeto, (list, tuple, set, frozenset)):
        return any(_puede_por_contexto(actor, accion, item) for item in objeto)

    carrera_objeto = _coerce_carrera_id(objeto)
    if carrera_objeto is None:
        return True

    return carrera_objeto in _ids_carrera_del_usuario(actor)


def puede(actor, accion, objeto=None, *, recurso=None, contexto=None):
    if actor is None:
        return False

    if recurso is not None and objeto is None:
        objeto = recurso

    nombre_accion = _normalizar_token(accion)
    if nombre_accion.startswith("ciclos_"):
        nombre_accion = nombre_accion[len("ciclos_") :]
    if nombre_accion.startswith("ciclos."):
        nombre_accion = nombre_accion.split(".", 1)[1]

    roles_requeridos = _PERMISOS_POR_ACCION.get(nombre_accion)
    if roles_requeridos is None:
        return True

    roles = set(_iterar_roles(actor))
    if "administrador_tecnico" in roles:
        return True

    if "director_carrera" not in roles:
        return False
    if "director_carrera" not in roles_requeridos:
        return False

    if objeto is None:
        return True

    if _puede_por_contexto(actor, nombre_accion, objeto):
        return True

    permisos = set()
    permisos.update(_normalizar_token(p) for p in getattr(actor, "permissions", []) if p)
    permisos.update(_normalizar_token(p) for p in getattr(actor, "permission", []) if p)
    permisos.update(_normalizar_token(p) for p in getattr(actor, "permisos", []) if p)
    aliases = {
        "crear_facultad": {"facultad.crear", "crear_facultad", "facultad_crear"},
        "crear_carrera": {"carrera.crear", "crear_carrera", "carrera_crear"},
        "abrir_ciclo": {"ciclo.abrir", "abrir_ciclo", "ciclo_abrir"},
        "cerrar_ciclo": {"ciclo.cerrar", "cerrar_ciclo", "ciclo_cerrar"},
        "asignar_dimension": {"dimension.asignar", "asignar_dimension", "dimension_asignar"},
        "quitar_asignacion": {"dimension.quitar", "quitar_asignacion", "dimension_quitar"},
    }
    if nombre_accion in aliases:
        if permisos.intersection(aliases[nombre_accion]):
            return True

    return False


__all__ = ["PermisoSistema", "puede"]
