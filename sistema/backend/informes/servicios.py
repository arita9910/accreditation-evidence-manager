from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max

from analisis.servicios import completitud
from auditoria.servicios import registrar
from ciclos.servicios import exigir_ciclo_abierto
from cuentas.permisos import puede
from nucleo import almacenamiento

from .generador import contar_paginas, generar_docx
from .modelos import SECCIONES_INFORME_DOCUMENTADAS, TextoInforme, VersionInforme


def guardar_texto(ciclo, seccion, contenido, usuario):
    if usuario is None or not puede(usuario, "guardar_texto_informe", objeto=ciclo):
        raise ValidationError("No tiene permiso para editar el informe.")
    exigir_ciclo_abierto(ciclo)
    if seccion not in SECCIONES_INFORME_DOCUMENTADAS:
        raise ValidationError("La sección del informe no es válida.")
    if contenido is None:
        raise ValidationError("El contenido del informe es obligatorio.")

    with transaction.atomic():
        texto, creado = TextoInforme.objects.update_or_create(
            ciclo=ciclo,
            seccion=seccion,
            defaults={
                "contenido": str(contenido),
                "editado_por": usuario,
                "modificado_por": usuario,
            },
        )
        registrar(
            "guardar_texto_informe",
            usuario=usuario,
            entidad="TextoInforme",
            detalle={
                "id": texto.pk,
                "ciclo_id": ciclo.pk,
                "seccion": seccion,
                "creado": creado,
            },
        )
    return texto


def generar_version(ciclo, usuario):
    if usuario is None or not puede(usuario, "generar_informe", objeto=ciclo):
        raise ValidationError("No tiene permiso para generar el informe.")
    exigir_ciclo_abierto(ciclo)

    with transaction.atomic():
        ciclo_bloqueado = (
            ciclo.__class__.objects.select_for_update().select_related("carrera").get(pk=ciclo.pk)
        )
        resultado_completitud = completitud(ciclo_bloqueado, usuario=usuario)
        if hasattr(resultado_completitud, "to_dict"):
            avisos = resultado_completitud.to_dict()
        elif isinstance(resultado_completitud, dict):
            avisos = resultado_completitud
        else:
            avisos = {}

        ruta_docx = generar_docx(ciclo_bloqueado)
        textos = TextoInforme.objects.filter(ciclo=ciclo_bloqueado).values_list("contenido", flat=True)
        paginas, metodo = contar_paginas(ruta_docx, contenido_cuerpo="\n".join(textos))
        avisos_payload = {
            "completitud": avisos,
            "paginas": paginas,
        }
        if paginas > 50:
            avisos_payload["advertencia"] = "El cuerpo del informe supera las 50 páginas."

        numero_actual = (
            VersionInforme.objects.select_for_update()
            .filter(ciclo=ciclo_bloqueado)
            .aggregate(maximo=Max("numero"))["maximo"]
            or 0
        )
        numero = numero_actual + 1

        with ruta_docx.open("rb") as archivo:
            almacenado = almacenamiento.guardar_fichero(
                archivo,
                f"informes/{ciclo_bloqueado.pk}",
            )

        try:
            ruta_docx.unlink()
        except FileNotFoundError:
            pass

        version = VersionInforme.objects.create(
            ciclo=ciclo_bloqueado,
            numero=numero,
            fichero=almacenado["ruta_relativa"],
            sha256=almacenado["sha256"],
            paginas=paginas,
            metodo_conteo=metodo,
            avisos=avisos_payload,
            creado_por=usuario,
            modificado_por=usuario,
        )
        registrar(
            "generar_informe",
            usuario=usuario,
            entidad="VersionInforme",
            detalle={
                "id": version.pk,
                "ciclo_id": ciclo_bloqueado.pk,
                "numero": numero,
                "sha256": version.sha256,
                "paginas": paginas,
                "metodo_conteo": metodo,
            },
        )
    return version


__all__ = ["guardar_texto", "generar_version"]
