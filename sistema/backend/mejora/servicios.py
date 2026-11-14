from __future__ import annotations

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


def registrar_seguimiento(accion, avance, nota, usuario=None):
    if accion is None:
        raise ValidationError("Debe indicar una acción válida.")
    if usuario is None:
        raise ValidationError("Debe indicar un usuario válido.")

    exigir_ciclo_abierto(accion.plan.ciclo)
    _requerir_permiso("registrar_seguimiento", usuario, accion.plan.ciclo)

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


__all__ = [
    "crear_plan_mejora",
    "crear_accion_mejora",
    "registrar_seguimiento",
    "vincular_evidencia",
]
