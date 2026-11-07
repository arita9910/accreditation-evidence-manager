from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import AsignacionDimension, Carrera, Ciclo, Facultad


def crear_facultad(nombre):
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValidationError("El nombre de la facultad es obligatorio.")
    return Facultad.objects.create(nombre=nombre)


def crear_carrera(facultad, nombre, activa=True):
    if facultad is None:
        raise ValidationError("Debe indicarse una facultad válida.")
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValidationError("El nombre de la carrera es obligatorio.")
    return Carrera.objects.create(facultad=facultad, nombre=nombre, activa=activa)


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
):
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
    return ciclo


def cerrar_ciclo(ciclo, categoria_obtenida=None, vigencia_anios=None):
    if ciclo is None:
        raise ValidationError("Debe indicar un ciclo válido.")
    if ciclo.estado == Ciclo.Estado.CERRADO:
        raise ValidationError("El ciclo ya está cerrado y no puede modificarse.")
    if vigencia_anios is not None and vigencia_anios not in (5, 7, 9):
        raise ValidationError("La vigencia debe ser 5, 7, 9 o nula.")

    ciclo.estado = Ciclo.Estado.CERRADO
    ciclo.fecha_cierre = timezone.localdate()
    if categoria_obtenida is not None:
        ciclo.categoria_obtenida = str(categoria_obtenida).strip() or None
    if vigencia_anios is not None:
        ciclo.vigencia_anios = vigencia_anios
    ciclo.full_clean()
    ciclo.save()
    return ciclo


def asignar_dimension(ciclo, usuario, dimension):
    exigir_ciclo_abierto(ciclo)
    if usuario is None:
        raise ValidationError("Debe indicarse un usuario válido.")
    if dimension is None:
        raise ValidationError("Debe indicarse una dimensión válida.")

    carrera = ciclo.carrera
    try:
        related = getattr(carrera, "usuarios")
    except AttributeError:
        related = None
    if related is not None and not related.filter(pk=usuario.pk).exists():
        raise ValidationError("El usuario no pertenece a la carrera del ciclo.")

    if AsignacionDimension.objects.filter(
        ciclo=ciclo,
        usuario=usuario,
        dimension=dimension,
    ).exists():
        raise ValidationError("La asignación ya existe para este usuario y dimensión.")

    return AsignacionDimension.objects.create(
        ciclo=ciclo,
        usuario=usuario,
        dimension=dimension,
    )


def quitar_asignacion(ciclo, usuario, dimension):
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

    return registros.delete()[0]


__all__ = [
    "crear_facultad",
    "crear_carrera",
    "exigir_ciclo_abierto",
    "abrir_ciclo",
    "cerrar_ciclo",
    "asignar_dimension",
    "quitar_asignacion",
]
