from __future__ import annotations

from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction

from auditoria.servicios import registrar
from ciclos.servicios import exigir_ciclo_abierto
from cuentas.permisos import puede

from .models import AccionEvidencia, AccionMejora, PlanMejora, SeguimientoAccion


def _requerir_permiso(accion, actor, objeto=None):
    if actor is None:
        return
    if not puede(actor, accion, objeto=objeto):
        raise ValidationError("No tiene permiso para realizar esta acción.")


def _validar_transicion(estado_actual, estado_nuevo):
    transiciones = {
        AccionMejora.Estado.PROPUESTA: {AccionMejora.Estado.APROBADA},
        AccionMejora.Estado.APROBADA: {AccionMejora.Estado.EN_CURSO},
        AccionMejora.Estado.EN_CURSO: {
            AccionMejora.Estado.CUMPLIDA,
            AccionMejora.Estado.NO_CUMPLIDA,
        },
    }
    return estado_nuevo in transiciones.get(estado_actual, set())


def _validar_usuario_seguimiento(accion, usuario):
    if usuario is None:
        raise ValidationError("Debe indicar un usuario válido.")
    if getattr(usuario, "pk", None) == getattr(accion.responsable, "pk", None):
        return
    if getattr(usuario, "rol", None) in {"director_carrera", "administrador_tecnico"}:
        return
    raise ValidationError("Solo el responsable de la acción o un director puede registrar seguimiento.")


def crear_plan_mejora(ciclo, usuario=None):
    if ciclo is None:
        raise ValidationError("Debe indicar un ciclo válido.")
    exigir_ciclo_abierto(ciclo)
    _requerir_permiso("crear_plan_mejora", usuario, ciclo)
    if PlanMejora.objects.filter(ciclo=ciclo).exists():
        raise ValidationError("Ya existe un plan de mejora para este ciclo.")

    with transaction.atomic():
        plan = PlanMejora.objects.create(ciclo=ciclo)
        registrar(
            "crear_plan_mejora",
            usuario=usuario,
            entidad="PlanMejora",
            detalle={"id": plan.pk, "ciclo_id": ciclo.pk},
        )
    return plan


def proponer_accion(plan, debilidad, descripcion, responsable, fecha_limite, usuario=None):
    return crear_accion_mejora(
        plan,
        debilidad,
        descripcion,
        responsable,
        fecha_limite,
        usuario=usuario,
    )


def crear_accion_mejora(plan, debilidad, descripcion, responsable, fecha_limite, usuario=None):
    if plan is None:
        raise ValidationError("Debe indicar un plan válido.")
    if debilidad is None:
        raise ValidationError("Debe indicar una debilidad válida.")
    if responsable is None:
        raise ValidationError("Debe indicar un responsable válido.")
    if fecha_limite is None:
        raise ValidationError("Debe indicar una fecha límite.")

    exigir_ciclo_abierto(plan.ciclo)
    _requerir_permiso("proponer_accion", usuario, plan.ciclo)

    accion = AccionMejora(
        plan=plan,
        debilidad=debilidad,
        descripcion=(descripcion or "").strip(),
        responsable=responsable,
        fecha_limite=fecha_limite,
    )
    if not accion.descripcion:
        raise ValidationError("La descripción de la acción de mejora es obligatoria.")

    with transaction.atomic():
        accion.full_clean()
        accion.save()
        registrar(
            "crear_accion_mejora",
            usuario=usuario,
            entidad="AccionMejora",
            detalle={
                "id": accion.pk,
                "plan_id": plan.pk,
                "debilidad_id": debilidad.pk,
                "responsable_id": responsable.pk,
                "fecha_limite": str(fecha_limite),
            },
        )
    return accion


def cambiar_estado_accion(accion, nuevo_estado, usuario=None, nota=None):
    if accion is None:
        raise ValidationError("Debe indicar una acción válida.")
    if usuario is None:
        raise ValidationError("Debe indicar un usuario válido.")
    if nuevo_estado is None:
        raise ValidationError("Debe indicar un estado válido.")
    if nuevo_estado not in {estado.value for estado in AccionMejora.Estado}:
        raise ValidationError("El estado indicado no es válido.")

    exigir_ciclo_abierto(accion.plan.ciclo)
    _requerir_permiso("aprobar_accion", usuario, accion.plan.ciclo)

    if not _validar_transicion(accion.estado, nuevo_estado):
        raise ValidationError("La acción no puede pasar al estado solicitado desde su estado actual.")

    with transaction.atomic():
        estado_anterior = accion.estado
        accion.estado = nuevo_estado
        accion.save()
        registro = SeguimientoAccion.objects.create(
            accion=accion,
            avance=0,
            nota=(nota or f"Cambio de estado a {nuevo_estado}."),
            registrado_por=usuario,
        )
        registrar(
            "cambiar_estado_accion",
            usuario=usuario,
            entidad="AccionMejora",
            detalle={
                "id": accion.pk,
                "estado_anterior": estado_anterior,
                "estado_nuevo": nuevo_estado,
                "seguimiento_id": registro.pk,
            },
        )
    return accion


def aprobar_accion(accion, usuario=None, nota=None):
    if accion is None:
        raise ValidationError("Debe indicar una acción válida.")
    if usuario is None:
        raise ValidationError("Debe indicar un usuario válido.")

    return cambiar_estado_accion(
        accion,
        AccionMejora.Estado.APROBADA,
        usuario=usuario,
        nota=nota or "Aprobación de la acción de mejora.",
    )


def registrar_seguimiento(accion, avance, nota, usuario=None):
    if accion is None:
        raise ValidationError("Debe indicar una acción válida.")
    if usuario is None:
        raise ValidationError("Debe indicar un usuario válido.")

    exigir_ciclo_abierto(accion.plan.ciclo)
    _requerir_permiso("registrar_seguimiento", usuario, accion.plan.ciclo)
    _validar_usuario_seguimiento(accion, usuario)

    seguimiento = SeguimientoAccion(
        accion=accion,
        avance=avance,
        nota=(nota or "").strip(),
        registrado_por=usuario,
    )

    with transaction.atomic():
        seguimiento.full_clean()
        seguimiento.save()
        registrar(
            "registrar_seguimiento",
            usuario=usuario,
            entidad="SeguimientoAccion",
            detalle={
                "id": seguimiento.pk,
                "accion_id": accion.pk,
                "avance": seguimiento.avance,
            },
        )
    return seguimiento


def vincular_evidencia(accion, evidencia, usuario=None):
    if accion is None:
        raise ValidationError("Debe indicar una acción válida.")
    if evidencia is None:
        raise ValidationError("Debe indicar una evidencia válida.")

    exigir_ciclo_abierto(accion.plan.ciclo)
    _requerir_permiso("vincular_evidencia", usuario, accion.plan.ciclo)

    relacion = AccionEvidencia(accion=accion, evidencia=evidencia)
    with transaction.atomic():
        relacion.full_clean()
        relacion.save()
        registrar(
            "vincular_evidencia",
            usuario=usuario,
            entidad="AccionEvidencia",
            detalle={"id": relacion.pk, "accion_id": accion.pk, "evidencia_id": evidencia.pk},
        )
    return relacion


def acciones_vencidas(plan):
    if plan is None:
        raise ValidationError("Debe indicar un plan válido.")
    estado_final = {
        AccionMejora.Estado.CUMPLIDA,
        AccionMejora.Estado.NO_CUMPLIDA,
    }
    return AccionMejora.objects.filter(
        plan=plan,
        fecha_limite__lt=date.today(),
    ).exclude(estado__in=estado_final)


def plan_ciclo_anterior(ciclo):
    if ciclo is None:
        raise ValidationError("Debe indicar un ciclo válido.")
    ciclo_anterior = getattr(ciclo, "ciclo_anterior", None)
    if ciclo_anterior is None:
        return None
    return PlanMejora.objects.filter(ciclo=ciclo_anterior).select_related("ciclo").prefetch_related("acciones").first()


__all__ = [
    "crear_plan_mejora",
    "proponer_accion",
    "crear_accion_mejora",
    "cambiar_estado_accion",
    "aprobar_accion",
    "registrar_seguimiento",
    "vincular_evidencia",
    "acciones_vencidas",
    "plan_ciclo_anterior",
]
