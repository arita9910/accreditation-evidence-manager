import hashlib
import hmac
import os
from pathlib import Path, PureWindowsPath
import re
import tempfile
import uuid

from django.conf import settings


_TAMANO_BLOQUE = 1024 * 1024
_EXTENSION_SEGURA = re.compile(r"^[A-Za-z0-9]{1,16}$")


def _componentes_relativos(ruta):
    valor = os.fspath(ruta)
    if not isinstance(valor, str) or not valor:
        raise ValueError("La ruta relativa no puede estar vacía.")
    ruta_windows = PureWindowsPath(valor)
    if (
        Path(valor).is_absolute()
        or ruta_windows.is_absolute()
        or ruta_windows.drive
    ):
        raise ValueError("La ruta debe ser relativa.")

    componentes = valor.replace("\\", "/").split("/")
    if any(parte in {"", ".", ".."} for parte in componentes):
        raise ValueError("La ruta relativa contiene componentes no permitidos.")
    return componentes


def _ruta_evidencia(ruta_relativa):
    raiz = Path(settings.EVIDENCIAS_ROOT).resolve()
    destino = raiz.joinpath(*_componentes_relativos(ruta_relativa)).resolve()
    try:
        destino.relative_to(raiz)
    except ValueError as error:
        raise ValueError("La ruta debe permanecer dentro de EVIDENCIAS_ROOT.") from error
    return raiz, destino


def _iterar_bloques(archivo):
    chunks = getattr(archivo, "chunks", None)
    if callable(chunks):
        yield from chunks(chunk_size=_TAMANO_BLOQUE)
        return

    leer = getattr(archivo, "read", None)
    if not callable(leer):
        raise TypeError("El archivo debe permitir lectura por bloques.")

    while True:
        bloque = leer(_TAMANO_BLOQUE)
        if not bloque:
            break
        yield bloque


def _extension_archivo(archivo):
    nombre = getattr(archivo, "name", "")
    extension = PureWindowsPath(str(nombre)).suffix.lstrip(".")
    return f".{extension}" if _EXTENSION_SEGURA.fullmatch(extension) else ""


def guardar_fichero(archivo, subcarpeta):
    raiz = Path(settings.EVIDENCIAS_ROOT).resolve()
    componentes = _componentes_relativos(subcarpeta) if subcarpeta else []
    directorio = raiz.joinpath(*componentes).resolve()
    try:
        directorio.relative_to(raiz)
    except ValueError as error:
        raise ValueError("La carpeta debe permanecer dentro de EVIDENCIAS_ROOT.") from error

    directorio.mkdir(parents=True, exist_ok=True)
    directorio = directorio.resolve()
    try:
        directorio.relative_to(raiz)
    except ValueError as error:
        raise ValueError("La carpeta debe permanecer dentro de EVIDENCIAS_ROOT.") from error

    nombre_interno = f"{uuid.uuid4()}{_extension_archivo(archivo)}"
    ruta_relativa = Path(*componentes, nombre_interno).as_posix()
    _, destino = _ruta_evidencia(ruta_relativa)
    huella = hashlib.sha256()
    tamano = 0
    descriptor, ruta_temporal = tempfile.mkstemp(dir=directorio)

    try:
        with os.fdopen(descriptor, "wb") as salida:
            for bloque in _iterar_bloques(archivo):
                salida.write(bloque)
                huella.update(bloque)
                tamano += len(bloque)
        os.replace(ruta_temporal, destino)
    except Exception:
        try:
            os.unlink(ruta_temporal)
        except FileNotFoundError:
            pass
        raise

    return {
        "nombre_interno": nombre_interno,
        "ruta_relativa": ruta_relativa,
        "tamano": tamano,
        "sha256": huella.hexdigest(),
    }


def abrir_fichero(ruta_relativa):
    _, ruta = _ruta_evidencia(ruta_relativa)
    return ruta.open("rb")


def calcular_sha256(ruta):
    huella = hashlib.sha256()
    with abrir_fichero(ruta) as archivo:
        for bloque in iter(lambda: archivo.read(_TAMANO_BLOQUE), b""):
            huella.update(bloque)
    return huella.hexdigest()


def verificar_huella(ruta, sha256):
    return hmac.compare_digest(calcular_sha256(ruta), sha256)


def borrar_fichero(ruta_relativa):
    _, ruta = _ruta_evidencia(ruta_relativa)
    ruta.unlink()
