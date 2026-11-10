from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from auditoria.servicios import registrar
from cuentas.permisos import puede

from .models import AsignacionDimension, Carrera, Ciclo, Facultad


def _requerir_permiso(accion, actor, objeto=None):
    if actor is None:
        return
    if not puede(actor, accion, objeto=objeto):
        raise ValidationError("No tiene permiso para realizar esta acción.")


def crear_facultad(nombre, usuario=None):
    _requerir_permiso("crear_facultad", usuario)
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValidationError("El nombre de la facultad es obligatorio.")
    with transaction.atomic():
        facultad = Facultad.objects.create(nombre=nombre)
        registrar(
            "crear_facultad",
            usuario=usuario,
            entidad="Facultad",
            detalle={"id": facultad.pk, "nombre": facultad.nombre},
        )
    return facultad


def crear_carrera(facultad, nombre, activa=True, usuario=None):
    _requerir_permiso("crear_carrera", usuario)
    if facultad is None:
        raise ValidationError("Debe indicarse una facultad válida.")
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValidationError("El nombre de la carrera es obligatorio.")
    with transaction.atomic():
        carrera = Carrera.objects.create(facultad=facultad, nombre=nombre, activa=activa)
        registrar(
            "crear_carrera",
            usuario=usuario,
            entidad="Carrera",
            detalle={"id": carrera.pk, "nombre": carrera.nombre, "facultad_id": facultad.pk},
        )
    return carrera


def exigir_ciclo_abierto(ciclo):
    if ciclo is None:
        raise ValidationError("Debe indicar un ciclo válido.")
    if getattr(ciclo, "estado", None) != Ciclo.Estado.ABIERTO:
        raise ValidationError("El ciclo debe estar abierto para realizar esta operación.")
    return ciclo


def abrir_ciclo(
    carrera,
    tipo,
    anio_base,
    curso_inicial,
    version_normativa,
    ciclo_anterior=None,
    usuario=None,
):
    _requerir_permiso("abrir_ciclo", usuario, carrera)
    if carrera is None:
        raise ValidationError("Debe indicarse una carrera válida.")
    if version_normativa is None:
        raise ValidationError("Debe indicarse una versión normativa válida.")
    if tipo is None or str(tipo).strip() == "":
        raise ValidationError("El tipo de ciclo es obligatorio.")
    if anio_base is None:
        raise ValidationError("El año base es obligatorio.")
    if curso_inicial is None:
        raise ValidationError("El curso inicial es obligatorio.")

    if Ciclo.objects.filter(carrera=carrera, estado=Ciclo.Estado.ABIERTO).exists():
        raise ValidationError("Ya existe un ciclo abierto para esta carrera.")

    if ciclo_anterior is not None:
        if ciclo_anterior.carrera_id != carrera.pk:
            raise ValidationError("El ciclo anterior debe pertenecer a la misma carrera.")
        if ciclo_anterior.estado != Ciclo.Estado.CERRADO:
            raise ValidationError("El ciclo anterior debe estar cerrado.")

    curso_final = curso_inicial + 4
    with transaction.atomic():
        ciclo = Ciclo(
            carrera=carrera,
            version_normativa=version_normativa,
            tipo=str(tipo).strip(),
            anio_base=anio_base,
            curso_inicial=curso_inicial,
            curso_final=curso_final,
            estado=Ciclo.Estado.ABIERTO,
            ciclo_anterior=ciclo_anterior,
            fecha_apertura=timezone.localdate(),
        )
        ciclo.full_clean()
        ciclo.save()
        registrar(
            "abrir_ciclo",
            usuario=usuario,
            entidad="Ciclo",
            detalle={"id": ciclo.pk, "carrera_id": carrera.pk, "tipo": ciclo.tipo},
        )
    return ciclo


def cerrar_ciclo(ciclo, categoria_obtenida=None, vigencia_anios=None, usuario=None):
    _requerir_permiso("cerrar_ciclo", usuario, ciclo)
    if ciclo is None:
        raise ValidationError("Debe indicar un ciclo válido.")
    if ciclo.estado == Ciclo.Estado.CERRADO:
        raise ValidationError("El ciclo ya está cerrado y no puede modificarse.")
    if vigencia_anios is not None and vigencia_anios not in (5, 7, 9):
        raise ValidationError("La vigencia debe ser 5, 7, 9 o nula.")

    with transaction.atomic():
        ciclo.estado = Ciclo.Estado.CERRADO
        ciclo.fecha_cierre = timezone.localdate()
        if categoria_obtenida is not None:
            ciclo.categoria_obtenida = str(categoria_obtenida).strip() or None
        if vigencia_anios is not None:
            ciclo.vigencia_anios = vigencia_anios
        ciclo.full_clean()
        ciclo.save()
        registrar(
            "cerrar_ciclo",
            usuario=usuario,
            entidad="Ciclo",
            detalle={"id": ciclo.pk, "categoria_obtenida": ciclo.categoria_obtenida, "vigencia_anios": ciclo.vigencia_anios},
        )
    return ciclo


def asignar_dimension(ciclo, usuario, dimension, actor=None):
    _requerir_permiso("asignar_dimension", actor, ciclo)
    exigir_ciclo_abierto(ciclo)
    if usuario is None:
        raise ValidationError("Debe indicarse un usuario válido.")
    if dimension is None:
        raise ValidationError("Debe indicarse una dimensión válida.")

    carrera = ciclo.carrera
    usuario_carrera_id = getattr(usuario, "carrera_id", None)
    if usuario_carrera_id is not None and usuario_carrera_id != carrera.pk:
        raise ValidationError("El usuario no pertenece a la carrera del ciclo.")

    if AsignacionDimension.objects.filter(
        ciclo=ciclo,
        usuario=usuario,
        dimension=dimension,
    ).exists():
        raise ValidationError("La asignación ya existe para este usuario y dimensión.")

    with transaction.atomic():
        asignacion = AsignacionDimension.objects.create(
            ciclo=ciclo,
            usuario=usuario,
            dimension=dimension,
        )
        registrar(
            "asignar_dimension",
            usuario=actor or usuario,
            entidad="AsignacionDimension",
            detalle={"id": asignacion.pk, "ciclo_id": ciclo.pk, "usuario_id": usuario.pk, "dimension_id": dimension.pk},
        )
    return asignacion


def quitar_asignacion(ciclo, usuario, dimension, actor=None):
    _requerir_permiso("quitar_asignacion", actor, ciclo)
    exigir_ciclo_abierto(ciclo)
    if usuario is None:
        raise ValidationError("Debe indicarse un usuario válido.")
    if dimension is None:
        raise ValidationError("Debe indicarse una dimensión válida.")

    registros = AsignacionDimension.objects.filter(
        ciclo=ciclo,
        usuario=usuario,
        dimension=dimension,
    )
    if not registros.exists():
        return 0

    with transaction.atomic():
        total = registros.delete()[0]
        registrar(
            "quitar_asignacion",
            usuario=actor or usuario,
            entidad="AsignacionDimension",
            detalle={"ciclo_id": ciclo.pk, "usuario_id": usuario.pk, "dimension_id": dimension.pk, "eliminados": total},
        )
    return total


__all__ = [
    "crear_facultad",
    "crear_carrera",
    "exigir_ciclo_abierto",
    "abrir_ciclo",
    "cerrar_ciclo",
    "asignar_dimension",
    "quitar_asignacion",
]
