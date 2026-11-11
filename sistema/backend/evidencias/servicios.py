from __future__ import annotations

import mimetypes
import uuid
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import UploadedFile
from django.db import transaction
from django.http import FileResponse

from auditoria.servicios import registrar
from ciclos.servicios import exigir_ciclo_abierto
from cuentas.permisos import puede
from estructura.models import Criterio, TipoEvidencia
from nucleo.almacenamiento import guardar_fichero
from nucleo.almacenamiento import verificar_huella as verificar_huella_almacenamiento

from .modelos import Clasificacion, Evidencia, FicheroEvidencia

EXTENSIONES_PERMITIDAS = {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".txt",
    ".csv",
    ".zip",
    ".odt",
    ".ods",
    ".odp",
    ".rtf",
    ".xml",
    ".html",
}

# Límite inicial propuesto para evidencias digitales. Se revisará con las entrevistas; por ahora
# se mantiene razonable para evitar archivos excesivamente grandes en el almacenamiento interno.
TAMANO_MAXIMO_BYTES = 25 * 1024 * 1024


def _resolver_tipo_evidencia(valor):
    if valor is None:
        raise ValidationError("Debe indicarse el tipo de evidencia.")
    if isinstance(valor, TipoEvidencia):
        return valor
    if hasattr(valor, "pk"):
        return TipoEvidencia.objects.get(pk=valor.pk)
    return TipoEvidencia.objects.get(pk=valor)


def _resolver_evidencia(valor):
    if valor is None:
        raise ValidationError("Debe indicarse una evidencia válida.")
    if isinstance(valor, Evidencia):
        return valor
    return Evidencia.objects.get(pk=valor)


def _resolver_fichero(valor):
    if valor is None:
        raise ValidationError("Debe indicarse un fichero válido.")
    if isinstance(valor, FicheroEvidencia):
        return valor
    return FicheroEvidencia.objects.get(pk=valor)


def _obtener_usuario(usuario=None, **kwargs):
    if usuario is not None:
        return usuario
    if kwargs.get("usuario") is not None:
        return kwargs["usuario"]
    return get_user_model().objects.order_by("pk").first()


def _normalizar_soporte(valor):
    soporte = str(valor or "").strip().lower()
    if soporte in {"digital", "digitales", Evidencia.Soporte.DIGITAL}:
        return Evidencia.Soporte.DIGITAL
    if soporte in {"papel", Evidencia.Soporte.PAPEL}:
        return Evidencia.Soporte.PAPEL
    raise ValidationError("El soporte debe ser 'digital' o 'papel'.")


def _extension_nombre(nombre):
    return Path(str(nombre)).suffix.lower()


def _ruta_relativa_fichero(fichero):
    extension = _extension_nombre(fichero.nombre_original)
    nombre_archivo = f"{fichero.nombre_interno}{extension}"
    return Path("ciclos") / str(fichero.evidencia_id) / "evidencias" / nombre_archivo


def _ruta_absoluta_fichero(fichero):
    return Path(settings.EVIDENCIAS_ROOT) / _ruta_relativa_fichero(fichero)


def _validar_archivo(archivo, *, permitir_vacio=False):
    if archivo is None:
        if permitir_vacio:
            return None
        raise ValidationError("Debe adjuntar un fichero para una evidencia digital.")

    nombre = getattr(archivo, "name", "") or "archivo.bin"
    extension = Path(str(nombre)).suffix.lower()
    if extension and extension not in EXTENSIONES_PERMITIDAS:
        raise ValidationError(
            "El tipo de fichero no está permitido. Extensiones válidas: "
            + ", ".join(sorted(EXTENSIONES_PERMITIDAS))
        )

    tamano = getattr(archivo, "size", None)
    if tamano is None:
        try:
            posicion = archivo.tell()
            archivo.seek(0, 2)
            tamano = archivo.tell()
            archivo.seek(posicion)
        except (AttributeError, OSError, ValueError):
            tamano = 0

    tamano = int(tamano or 0)
    if tamano <= 0:
        raise ValidationError("El archivo está vacío.")
    if tamano > TAMANO_MAXIMO_BYTES:
        raise ValidationError(
            f"El tamaño del archivo supera el límite de {TAMANO_MAXIMO_BYTES // (1024 * 1024)} MB."
        )

    tipo_mime = getattr(archivo, "content_type", None) or mimetypes.guess_type(nombre)[0]
    if not tipo_mime:
        tipo_mime = "application/octet-stream"

    return {
        "nombre_original": str(nombre),
        "tamano": tamano,
        "tipo_mime": str(tipo_mime),
    }


def _validar_datos_evidencia(ciclo, datos, archivo=None):
    if ciclo is None:
        raise ValidationError("Debe indicarse un ciclo válido.")
    exigir_ciclo_abierto(ciclo)

    datos = dict(datos or {})
    if not datos.get("titulo") and hasattr(datos.get("titulo", None), "strip"):
        pass

    titulo = str(datos.get("titulo") or "").strip()
    if not titulo:
        raise ValidationError("El título de la evidencia es obligatorio.")

    tipo = datos.get("tipo_evidencia")
    if tipo is None:
        tipo = datos.get("tipo")
    if tipo is None:
        tipo = datos.get("tipo_evidencia_id")
    if tipo is None:
        raise ValidationError("Debe indicar el tipo de evidencia.")
    tipo_evidencia = _resolver_tipo_evidencia(tipo)

    soporte = _normalizar_soporte(datos.get("soporte"))

    curso_academico = datos.get("curso_academico")
    if curso_academico in (None, ""):
        raise ValidationError("El curso académico es obligatorio.")
    try:
        curso_academico = int(curso_academico)
    except (TypeError, ValueError):
        raise ValidationError("El curso académico debe ser numérico.") from None
    if curso_academico <= 0:
        raise ValidationError("El curso académico debe ser válido.")

    desde = datos.get("periodo_desde") or datos.get("fecha_desde")
    hasta = datos.get("periodo_hasta") or datos.get("fecha_hasta")
    if desde in (None, "") or hasta in (None, ""):
        raise ValidationError("El periodo de la evidencia es obligatorio.")

    custodia_original = str(datos.get("custodia_original") or "").strip()
    if soporte == Evidencia.Soporte.PAPEL and not custodia_original:
        raise ValidationError("La custodia original es obligatoria para evidencias en papel.")

    if soporte == Evidencia.Soporte.DIGITAL:
        _validar_archivo(archivo)

    return {
        "titulo": titulo,
        "tipo_evidencia": tipo_evidencia,
        "soporte": soporte,
        "curso_academico": curso_academico,
        "periodo_desde": desde,
        "periodo_hasta": hasta,
        "custodia_original": custodia_original,
    }


def crear_evidencia(ciclo, datos=None, archivo=None, usuario=None, **kwargs):
    ciclo = ciclo or kwargs.get("ciclo")
    if datos is None:
        datos = kwargs
    elif isinstance(datos, dict):
        datos = {**datos, **kwargs}
    else:
        datos = {
            "titulo": getattr(datos, "titulo", None),
            "tipo_evidencia": getattr(datos, "tipo_evidencia", None),
            "tipo": getattr(datos, "tipo", None),
            "soporte": getattr(datos, "soporte", None),
            "curso_academico": getattr(datos, "curso_academico", None),
            "periodo_desde": getattr(datos, "periodo_desde", None),
            "periodo_hasta": getattr(datos, "periodo_hasta", None),
            "custodia_original": getattr(datos, "custodia_original", None),
            "usuario": getattr(datos, "usuario", None),
            **kwargs,
        }

    usuario = kwargs.get("usuario", usuario) or datos.get("usuario")
    validacion = _validar_datos_evidencia(ciclo, datos, archivo=archivo)
    if archivo is None and validacion["soporte"] == Evidencia.Soporte.DIGITAL:
        raise ValidationError("Debe incluir un fichero para la evidencia digital.")

    if archivo is not None and validacion["soporte"] == Evidencia.Soporte.PAPEL:
        raise ValidationError("La evidencia en papel no admite ficheros asociados.")

    usuario = _obtener_usuario(usuario=usuario)
    if usuario is None:
        raise ValidationError("Debe indicar el usuario que registra la evidencia.")

    with transaction.atomic():
        evidencia = Evidencia.objects.create(
            ciclo=ciclo,
            tipo_evidencia=validacion["tipo_evidencia"],
            titulo=validacion["titulo"],
            descripcion=str(datos.get("descripcion") or ""),
            curso_academico=validacion["curso_academico"],
            periodo_desde=validacion["periodo_desde"],
            periodo_hasta=validacion["periodo_hasta"],
            soporte=validacion["soporte"],
            custodia_original=validacion["custodia_original"],
        )

        if archivo is not None:
            informacion = _validar_archivo(archivo)
            ruta_guardada = guardar_fichero(
                archivo,
                subcarpeta=f"ciclos/{evidencia.pk}/evidencias",
            )
            nombre_interno = str(uuid.uuid4())
            origen = Path(settings.EVIDENCIAS_ROOT) / ruta_guardada["ruta_relativa"]
            destino = origen.with_name(f"{nombre_interno}{origen.suffix}")
            origen.replace(destino)
            fichero = FicheroEvidencia.objects.create(
                evidencia=evidencia,
                version=1,
                nombre_original=informacion["nombre_original"],
                nombre_interno=nombre_interno,
                tamano=informacion["tamano"],
                tipo_mime=informacion["tipo_mime"],
                sha256=ruta_guardada["sha256"],
                vigente=True,
                subido_por=usuario,
            )
            registrar(
                "crear_evidencia",
                usuario=usuario,
                entidad="Evidencia",
                detalle={
                    "id": evidencia.pk,
                    "titulo": evidencia.titulo,
                    "fichero_id": fichero.pk,
                    "sha256": fichero.sha256,
                },
                contexto={"ciclo_id": ciclo.pk, "soporte": evidencia.soporte},
            )
        else:
            registrar(
                "crear_evidencia",
                usuario=usuario,
                entidad="Evidencia",
                detalle={"id": evidencia.pk, "titulo": evidencia.titulo},
                contexto={"ciclo_id": ciclo.pk, "soporte": evidencia.soporte},
            )

    return evidencia


def reemplazar_fichero(evidencia, archivo, usuario=None):
    evidencia = _resolver_evidencia(evidencia)
    exigir_ciclo_abierto(evidencia.ciclo)
    if evidencia.soporte == Evidencia.Soporte.PAPEL:
        raise ValidationError("La evidencia en papel no admite ficheros asociados.")
    informacion = _validar_archivo(archivo)
    usuario = _obtener_usuario(usuario=usuario)
    if usuario is None:
        raise ValidationError("Debe indicar el usuario que reemplaza el fichero.")

    with transaction.atomic():
        anterior = evidencia.ficheros.filter(vigente=True).order_by("-version").first()
        if anterior is not None:
            anterior.vigente = False
            anterior.save(update_fields=["vigente"])

        ruta_guardada = guardar_fichero(
            archivo,
            subcarpeta=f"ciclos/{evidencia.pk}/evidencias",
        )
        nombre_interno = str(uuid.uuid4())
        origen = Path(settings.EVIDENCIAS_ROOT) / ruta_guardada["ruta_relativa"]
        destino = origen.with_name(f"{nombre_interno}{origen.suffix}")
        origen.replace(destino)
        version = (anterior.version if anterior is not None else 0) + 1
        fichero = FicheroEvidencia.objects.create(
            evidencia=evidencia,
            version=version,
            nombre_original=informacion["nombre_original"],
            nombre_interno=nombre_interno,
            tamano=informacion["tamano"],
            tipo_mime=informacion["tipo_mime"],
            sha256=ruta_guardada["sha256"],
            vigente=True,
            subido_por=usuario,
        )
        registrar(
            "reemplazar_fichero",
            usuario=usuario,
            entidad="FicheroEvidencia",
            detalle={
                "evidencia_id": evidencia.pk,
                "version_anterior": anterior.version if anterior is not None else None,
                "version_nueva": fichero.version,
                "sha256": fichero.sha256,
            },
            contexto={"ciclo_id": evidencia.ciclo.pk, "fichero_id": fichero.pk},
        )

    return fichero


def verificar_huella(fichero):
    fichero = _resolver_fichero(fichero)
    ruta_relativa = _ruta_relativa_fichero(fichero)
    ruta_absoluta = Path(settings.EVIDENCIAS_ROOT) / ruta_relativa
    if not ruta_absoluta.exists():
        return "falta"
    try:
        if verificar_huella_almacenamiento(ruta_relativa.as_posix(), fichero.sha256):
            return "correcta"
        return "alterada"
    except FileNotFoundError:
        return "falta"


def clasificar(evidencia, criterios, usuario=None):
    evidencia = _resolver_evidencia(evidencia)
    usuario = _obtener_usuario(usuario=usuario)
    if usuario is None:
        raise ValidationError("Debe indicar el usuario que clasifica la evidencia.")
    if not isinstance(criterios, (list, tuple, set)):
        criterios = [criterios]

    resultados = []
    for criterio in criterios:
        if isinstance(criterio, Criterio):
            criterio_obj = criterio
        else:
            criterio_obj = Criterio.objects.get(pk=criterio)
        if criterio_obj.indicador.dimension.version_id != evidencia.ciclo.version_normativa_id:
            raise ValidationError(
                "El criterio debe pertenecer a la misma versión normativa del ciclo de la evidencia."
            )
        clasificacion, creada = Clasificacion.objects.get_or_create(
            evidencia=evidencia,
            criterio=criterio_obj,
            defaults={"clasificada_por": usuario},
        )
        if not creada:
            clasificacion.clasificada_por = usuario
            clasificacion.save(update_fields=["clasificada_por"])
        registrar(
            "clasificar_evidencia",
            usuario=usuario,
            entidad="Clasificacion",
            detalle={"evidencia_id": evidencia.pk, "criterio_id": criterio_obj.pk},
            contexto={"ciclo_id": evidencia.ciclo.pk},
        )
        resultados.append(clasificacion)
    return resultados[0] if len(resultados) == 1 else resultados


def quitar_clasificacion(evidencia, criterio, usuario=None):
    evidencia = _resolver_evidencia(evidencia)
    criterio_obj = criterio if isinstance(criterio, Criterio) else Criterio.objects.get(pk=criterio)
    clasificacion = evidencia.clasificaciones.filter(criterio=criterio_obj).first()
    if clasificacion is None:
        raise ValidationError("La evidencia no está clasificada en ese criterio.")
    clasificacion.delete()
    registrar(
        "quitar_clasificacion",
        usuario=_obtener_usuario(usuario=usuario),
        entidad="Clasificacion",
        detalle={"evidencia_id": evidencia.pk, "criterio_id": criterio_obj.pk},
        contexto={"ciclo_id": evidencia.ciclo.pk},
    )
    return True


def verificar_huellas(ciclo):
    ciclo = ciclo or getattr(ciclo, "ciclo", None)
    if ciclo is None:
        raise ValidationError("Debe indicarse un ciclo válido.")
    resultados = []
    correctas = 0
    alteradas = 0
    faltantes = 0

    for evidencia in Evidencia.objects.filter(ciclo=ciclo).prefetch_related("ficheros"):
        for fichero in evidencia.ficheros.all():
            estado = verificar_huella(fichero)
            resultados.append(
                {
                    "evidencia_id": evidencia.pk,
                    "fichero_id": fichero.pk,
                    "nombre_original": fichero.nombre_original,
                    "version": fichero.version,
                    "estado": estado,
                }
            )
            if estado == "correcta":
                correctas += 1
            elif estado == "alterada":
                alteradas += 1
            else:
                faltantes += 1

    return {
        "resultados": resultados,
        "total": len(resultados),
        "correctas": correctas,
        "alteradas": alteradas,
        "faltantes": faltantes,
    }


def descargar(fichero, usuario=None):
    fichero = _resolver_fichero(fichero)
    if fichero.evidencia.soporte == Evidencia.Soporte.PAPEL:
        raise ValidationError("La evidencia en papel no admite descarga de fichero.")
    if usuario is not None and hasattr(usuario, "is_authenticated") and not usuario.is_authenticated:
        raise PermissionDenied("Debe autenticarse para descargar la evidencia.")

    if usuario is not None and not puede(usuario, "descargar_evidencia", objeto=fichero.evidencia):
        raise PermissionDenied("No tiene permiso para descargar esta evidencia.")

    ruta = _ruta_absoluta_fichero(fichero)
    if not ruta.exists():
        raise FileNotFoundError("El fichero solicitado no existe.")

    exigir_ciclo_abierto(fichero.evidencia.ciclo)

    response = FileResponse(
        ruta.open("rb"),
        as_attachment=True,
        filename=fichero.nombre_original,
    )
    response["Content-Type"] = fichero.tipo_mime or mimetypes.guess_type(fichero.nombre_original)[0] or "application/octet-stream"
    registrar(
        "descargar_evidencia",
        usuario=usuario,
        entidad="FicheroEvidencia",
        detalle={
            "evidencia_id": fichero.evidencia_id,
            "fichero_id": fichero.pk,
            "version": fichero.version,
            "nombre_original": fichero.nombre_original,
        },
        contexto={"ciclo_id": fichero.evidencia.ciclo.pk},
    )
    return response


__all__ = [
    "EXTENSIONES_PERMITIDAS",
    "TAMANO_MAXIMO_BYTES",
    "crear_evidencia",
    "clasificar",
    "quitar_clasificacion",
    "reemplazar_fichero",
    "verificar_huella",
    "verificar_huellas",
    "descargar",
]
