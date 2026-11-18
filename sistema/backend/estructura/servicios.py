import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from django.conf import settings
from django.db import transaction

from .models import (
    Criterio,
    CriterioModelo,
    Dimension,
    EvidenciaSugerida,
    Indicador,
    ModeloCampo,
    ModeloDefinicion,
    RequisitoCategoria,
    VersionNormativa,
)


class ErrorCatalogo(ValueError):
    pass


class CamposObligatoriosFaltantes(ErrorCatalogo):
    def __init__(self, campos):
        self.campos = campos
        detalle = "\n".join(f"- {campo}" for campo in campos)
        super().__init__(f"Faltan campos obligatorios:\n{detalle}")


@dataclass(frozen=True)
class ReferenciaModelo:
    numero: int
    nota: str | None = None


_PREFIJO_DIMENSION = re.compile(r"^(\d+)\s+(.+)$")
_REFERENCIA_MODELO = re.compile(r"^M(\d+)(?:\s*\(([^()]+)\))?$")
_CATEGORIAS = (
    ("calificada", "requisito_calificada"),
    ("certificada", "requisito_certificada"),
    ("excelencia", "requisito_excelencia"),
    ("unica", "requisito_unico"),
)


def _ruta_predeterminada(nombre):
    return Path(settings.BASE_DIR).parent / "datos" / nombre


def _leer_json(ruta, descripcion):
    try:
        return json.loads(Path(ruta).read_text(encoding="utf-8"))
    except OSError as error:
        raise ErrorCatalogo(f"No se pudo leer {descripcion} en {ruta}: {error}") from error
    except UnicodeDecodeError as error:
        raise ErrorCatalogo(f"{descripcion} no está codificado en UTF-8 válido: {error}") from error
    except json.JSONDecodeError as error:
        raise ErrorCatalogo(
            f"{descripcion} no contiene JSON válido (línea {error.lineno}, "
            f"columna {error.colno}): {error.msg}"
        ) from error


def leer_catalogo(ruta=None):
    ruta = ruta or _ruta_predeterminada("catalogo_sea_cu_2025.json")
    datos = _leer_json(ruta, "el catálogo")
    _validar_estructura_catalogo(datos)
    return datos


def _validar_estructura_catalogo(datos):
    if not isinstance(datos, dict):
        raise ErrorCatalogo("La raíz del catálogo debe ser un objeto JSON.")
    for clave in ("catalogo", "version", "fuente", "dimensiones"):
        if clave not in datos:
            raise ErrorCatalogo(f"Falta la clave raíz «{clave}».")
    if not all(
        isinstance(datos[clave], str) and datos[clave].strip()
        for clave in ("catalogo", "version", "fuente")
    ):
        raise ErrorCatalogo("Las claves «catalogo», «version» y «fuente» deben contener texto.")
    if not isinstance(datos["dimensiones"], list):
        raise ErrorCatalogo("La clave «dimensiones» debe contener una lista.")

    totales = {"dimensiones": len(datos["dimensiones"]), "indicadores": 0, "criterios": 0}
    for indice_dimension, dimension in enumerate(datos["dimensiones"], start=1):
        ruta_dimension = f"dimensiones[{indice_dimension}]"
        if not isinstance(dimension, dict):
            raise ErrorCatalogo(f"{ruta_dimension} debe ser un objeto.")
        nombre = dimension.get("nombre")
        coincidencia = _PREFIJO_DIMENSION.match(nombre) if isinstance(nombre, str) else None
        if not coincidencia:
            raise ErrorCatalogo(
                f"{ruta_dimension}.nombre debe comenzar con un código numérico y un espacio."
            )
        codigo_dimension = coincidencia.group(1)
        if not isinstance(dimension.get("indicadores"), list):
            raise ErrorCatalogo(f"{ruta_dimension}.indicadores debe contener una lista.")

        for indice_indicador, indicador in enumerate(dimension["indicadores"], start=1):
            ruta_indicador = f"{ruta_dimension}.indicadores[{indice_indicador}]"
            if not isinstance(indicador, dict):
                raise ErrorCatalogo(f"{ruta_indicador} debe ser un objeto.")
            codigo_indicador = indicador.get("codigo")
            if not isinstance(codigo_indicador, str) or not re.fullmatch(
                rf"{re.escape(codigo_dimension)}\.\d+", codigo_indicador
            ):
                raise ErrorCatalogo(
                    f"{ruta_indicador}.codigo no corresponde al prefijo "
                    f"de la dimensión {codigo_dimension}."
                )
            if not isinstance(indicador.get("criterios"), list):
                raise ErrorCatalogo(f"{ruta_indicador}.criterios debe contener una lista.")
            totales["indicadores"] += 1
            for indice_criterio, criterio in enumerate(indicador["criterios"], start=1):
                ruta_criterio = f"{ruta_indicador}.criterios[{indice_criterio}]"
                if not isinstance(criterio, dict):
                    raise ErrorCatalogo(f"{ruta_criterio} debe ser un objeto.")
                for clave in (
                    "criterio",
                    "criterio_texto",
                    "codigo_guia",
                    "solo_en_guia",
                    "tipo_dato",
                    "requisito_por_categoria",
                ):
                    if clave not in criterio:
                        raise ErrorCatalogo(f"Falta la clave «{ruta_criterio}.{clave}».")
                if not isinstance(criterio["criterio"], str) or not isinstance(
                    criterio["criterio_texto"], str
                ):
                    raise ErrorCatalogo(f"{ruta_criterio} requiere códigos y texto.")
                if not re.fullmatch(
                    rf"{re.escape(codigo_indicador)}\.\d+", criterio["criterio"]
                ):
                    raise ErrorCatalogo(
                        f"{ruta_criterio}.criterio no corresponde al indicador "
                        f"{codigo_indicador}."
                    )
                totales["criterios"] += 1

    esperados = {"dimensiones": 6, "indicadores": 24, "criterios": 65}
    if totales != esperados:
        raise ErrorCatalogo(
            "Los totales del catálogo no son los esperados: "
            f"dimensiones={totales['dimensiones']}, "
            f"indicadores={totales['indicadores']}, criterios={totales['criterios']}; "
            "se esperan 6/24/65."
        )
    resumen = datos.get("resumen")
    if resumen is not None:
        if not isinstance(resumen, dict) or any(
            resumen.get(clave) != valor for clave, valor in esperados.items()
        ):
            raise ErrorCatalogo("El resumen del catálogo no coincide con los totales 6/24/65.")


def _booleano_catalogo(valor, ubicacion):
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str):
        normalizado = valor.strip().casefold()
        if normalizado == "sí":
            return True
        if normalizado == "no":
            return False
    raise ErrorCatalogo(f"{ubicacion} debe ser «sí» o «no».")


def _tipo_dato(valor, ubicacion):
    if not isinstance(valor, str):
        raise ErrorCatalogo(f"{ubicacion} debe ser «cualitativo» o «cuantitativo».")
    normalizado = valor.strip().casefold()
    if normalizado in (Criterio.TipoDato.CUALITATIVO, Criterio.TipoDato.CUANTITATIVO):
        return normalizado
    raise ErrorCatalogo(f"{ubicacion} contiene un tipo de dato no reconocido: {valor!r}.")


def _tipo_valor_modelo(valor, ubicacion):
    if not isinstance(valor, str):
        raise ErrorCatalogo(f"{ubicacion} debe indicar un tipo de valor de ModeloCampo.")
    normalizado = valor.strip().casefold()
    validos = {tipo for tipo, _ in ModeloCampo.TipoValor.choices}
    if normalizado in validos:
        return normalizado
    raise ErrorCatalogo(f"{ubicacion} contiene un tipo de valor no reconocido: {valor!r}.")


def _referencias_modelo(valor, ubicacion):
    if not isinstance(valor, str) or not valor.strip():
        return []
    referencias = []
    for parte in valor.split(","):
        coincidencia = _REFERENCIA_MODELO.fullmatch(parte.strip())
        if not coincidencia:
            raise ErrorCatalogo(f"Referencia de modelo no reconocida en {ubicacion}: {parte!r}.")
        referencias.append(
            ReferenciaModelo(
                numero=int(coincidencia.group(1)),
                nota=coincidencia.group(2).strip() if coincidencia.group(2) else None,
            )
        )
    return referencias


def _preparar_importacion(datos, datos_modelos):
    campos_faltantes = []
    fecha_texto = datos.get("fecha_aprobacion")
    if not isinstance(fecha_texto, str) or not fecha_texto.strip():
        campos_faltantes.append("fecha_aprobacion")
        fecha_aprobacion = None
    else:
        try:
            fecha_aprobacion = date.fromisoformat(fecha_texto)
        except ValueError as error:
            raise ErrorCatalogo("fecha_aprobacion debe tener formato AAAA-MM-DD.") from error

    if not isinstance(datos_modelos, dict) or not isinstance(datos_modelos.get("modelos"), list):
        raise ErrorCatalogo("modelos_resumen.json debe contener una lista «modelos».")
    modelos = {}
    for indice, modelo in enumerate(datos_modelos["modelos"], start=1):
        if not isinstance(modelo, dict):
            raise ErrorCatalogo(f"modelos[{indice}] debe ser un objeto.")
        codigo = modelo.get("codigo")
        numero = modelo.get("numero")
        nombre = modelo.get("nombre")
        valor_nombre = nombre.get("valor") if isinstance(nombre, dict) else None
        if not isinstance(codigo, str) or not re.fullmatch(r"M\d+", codigo):
            raise ErrorCatalogo(f"modelos[{indice}].codigo debe tener formato M<número>.")
        if not isinstance(numero, int) or numero <= 0 or int(codigo[1:]) != numero:
            raise ErrorCatalogo(f"modelos[{indice}] tiene un número que no coincide con {codigo}.")
        if not isinstance(valor_nombre, str) or not valor_nombre.strip():
            campos_faltantes.append(f"modelos[{indice}].nombre.valor")
            continue
        numero_rm36 = modelo.get("numero_rm36")
        celdas = modelo.get("celdas", {})
        if celdas is None:
            celdas = {}
        if not isinstance(celdas, dict):
            raise ErrorCatalogo(f"modelos[{indice}].celdas debe ser un objeto.")
        items_celdas = celdas.get("items", [])
        if not isinstance(items_celdas, list):
            raise ErrorCatalogo(f"modelos[{indice}].celdas.items debe ser una lista.")
        campos_modelo = []
        coordenadas = set()
        for indice_celda, celda in enumerate(items_celdas, start=1):
            ubicacion_celda = f"modelos[{indice}].celdas.items[{indice_celda}]"
            if not isinstance(celda, dict):
                raise ErrorCatalogo(f"{ubicacion_celda} debe ser un objeto.")
            fila = celda.get("fila")
            columna = celda.get("columna")
            orden = celda.get("orden", indice_celda)
            if not isinstance(fila, int) or fila <= 0:
                raise ErrorCatalogo(f"{ubicacion_celda}.fila debe ser un entero positivo.")
            if not isinstance(columna, int) or columna <= 0:
                raise ErrorCatalogo(f"{ubicacion_celda}.columna debe ser un entero positivo.")
            if not isinstance(orden, int) or orden <= 0:
                raise ErrorCatalogo(f"{ubicacion_celda}.orden debe ser un entero positivo.")
            etiqueta_fila = celda.get("etiqueta_fila")
            etiqueta_columna = celda.get("etiqueta_columna")
            if etiqueta_fila is not None and not isinstance(etiqueta_fila, str):
                raise ErrorCatalogo(f"{ubicacion_celda}.etiqueta_fila debe ser texto o nulo.")
            if etiqueta_columna is not None and not isinstance(etiqueta_columna, str):
                raise ErrorCatalogo(f"{ubicacion_celda}.etiqueta_columna debe ser texto o nulo.")
            coordenada = (fila, columna)
            if coordenada in coordenadas:
                raise ErrorCatalogo(
                    f"{ubicacion_celda} repite la coordenada fila={fila}, columna={columna}."
                )
            coordenadas.add(coordenada)
            campo = {
                "fila": fila,
                "columna": columna,
                "tipo_valor": _tipo_valor_modelo(
                    celda.get("tipo_valor"), f"{ubicacion_celda}.tipo_valor"
                ),
                "orden": orden,
            }
            if etiqueta_fila is not None:
                campo["etiqueta_fila"] = etiqueta_fila.strip()
            if etiqueta_columna is not None:
                campo["etiqueta_columna"] = etiqueta_columna.strip()
            campos_modelo.append(campo)
        modelos[numero] = {
            "nombre": valor_nombre.strip(),
            "numero_rm36": (
                numero_rm36.get("valor")
                if isinstance(numero_rm36, dict)
                else None
            ),
            "campos": campos_modelo,
        }

    dimensiones = []
    for indice_dimension, dimension in enumerate(datos["dimensiones"], start=1):
        coincidencia = _PREFIJO_DIMENSION.match(dimension["nombre"])
        codigo_dimension, nombre_dimension = coincidencia.groups()
        indicadores = []
        for indice_indicador, indicador in enumerate(dimension["indicadores"], start=1):
            texto = indicador.get("texto")
            if not isinstance(texto, str) or not texto.strip():
                campos_faltantes.append(
                    f"dimensiones[{indice_dimension}].indicadores[{indice_indicador}].texto"
                )
            criterios = []
            for indice_criterio, criterio in enumerate(indicador["criterios"], start=1):
                ubicacion = (
                    f"dimensiones[{indice_dimension}].indicadores[{indice_indicador}]"
                    f".criterios[{indice_criterio}]"
                )
                solo_en_guia = _booleano_catalogo(
                    criterio["solo_en_guia"], f"{ubicacion}.solo_en_guia"
                )
                codigo_manual = criterio.get("codigo_manual")
                if solo_en_guia or not isinstance(codigo_manual, str) or not codigo_manual.strip():
                    codigo_manual = None
                referencias = _referencias_modelo(
                    criterio.get("modelos_manual", ""), f"{ubicacion}.modelos_manual"
                )
                notas_modelos = [referencia.nota for referencia in referencias if referencia.nota]
                nota_normativa = str(criterio.get("nota_normativa", "")).strip()
                for nota in notas_modelos:
                    if nota not in nota_normativa:
                        nota_normativa = "\n".join(
                            valor for valor in (nota_normativa, nota) if valor
                        )
                requisitos = []
                for categoria, clave in _CATEGORIAS:
                    texto_requisito = criterio.get(clave, "")
                    if texto_requisito:
                        requisitos.append((categoria, texto_requisito))
                criterios.append(
                    {
                        "codigo": criterio["criterio"],
                        "codigo_manual": codigo_manual,
                        "codigo_guia": criterio["codigo_guia"],
                        "solo_en_guia": solo_en_guia,
                        "texto": criterio["criterio_texto"],
                        "tipo_dato": _tipo_dato(
                            criterio["tipo_dato"], f"{ubicacion}.tipo_dato"
                        ),
                        "valoracion_por_categoria": _booleano_catalogo(
                            criterio["requisito_por_categoria"],
                            f"{ubicacion}.requisito_por_categoria",
                        ),
                        "nota_normativa": nota_normativa,
                        "evidencias": [
                            texto.strip()
                            for texto in str(criterio.get("evidencias_guia", "")).split("|")
                            if texto.strip()
                        ],
                        "requisitos": requisitos,
                        "modelos": referencias,
                        "indicador_codigo": indicador["codigo"],
                    }
                )
            indicadores.append(
                {
                    "codigo": indicador["codigo"],
                    "texto": texto.strip() if isinstance(texto, str) else "",
                    "criterios": criterios,
                }
            )
        dimensiones.append(
            {"codigo": codigo_dimension, "nombre": nombre_dimension, "indicadores": indicadores}
        )

    if campos_faltantes:
        raise CamposObligatoriosFaltantes(campos_faltantes)
    if len(modelos) != 11:
        raise ErrorCatalogo(f"Se esperaban 11 modelos con nombre; se encontraron {len(modelos)}.")

    codigos_modelo = set(modelos)
    for dimension in dimensiones:
        for indicador in dimension["indicadores"]:
            for criterio in indicador["criterios"]:
                desconocidos = [
                    referencia.numero
                    for referencia in criterio["modelos"]
                    if referencia.numero not in codigos_modelo
                ]
                if desconocidos:
                    raise ErrorCatalogo(
                        f"{criterio['codigo']} referencia modelos inexistentes: "
                        + ", ".join(f"M{numero}" for numero in desconocidos)
                    )
    if not any(modelo["campos"] for modelo in modelos.values()):
        raise ErrorCatalogo("No se definieron celdas para ModeloCampo en los 11 modelos.")

    nombre_version = f"{datos['catalogo']} {datos['version']}".strip()
    return {
        "nombre_version": nombre_version,
        "fecha_aprobacion": fecha_aprobacion,
        "fuentes": datos["fuente"],
        "modelos": modelos,
        "dimensiones": dimensiones,
    }


def _crear_evidencias(criterio, evidencias):
    for orden, texto in enumerate(evidencias, start=1):
        inicial = texto.casefold()
        es_externa = inicial.startswith(("entrevista", "visita"))
        EvidenciaSugerida.objects.create(
            criterio=criterio,
            texto=texto,
            orden=orden,
            es_verificacion_externa=es_externa,
        )


def cargar_catalogo(ruta=None, ruta_modelos=None):
    datos = leer_catalogo(ruta)
    ruta_modelos = ruta_modelos or _ruta_predeterminada("modelos_resumen.json")
    datos_modelos = _leer_json(ruta_modelos, "el resumen de modelos")
    plan = _preparar_importacion(datos, datos_modelos)

    with transaction.atomic():
        version, _ = VersionNormativa.objects.update_or_create(
            nombre=plan["nombre_version"],
            defaults={
                "fecha_aprobacion": plan["fecha_aprobacion"],
                "fuentes": plan["fuentes"],
                "activa": True,
            },
        )
        modelos_guardados = {}
        for numero, datos_modelo in plan["modelos"].items():
            modelo, _ = ModeloDefinicion.objects.update_or_create(
                version=version,
                numero=numero,
                defaults={
                    "nombre": datos_modelo["nombre"],
                    "numero_rm36": datos_modelo["numero_rm36"],
                },
            )
            ids_campos_vigentes = []
            for datos_campo in datos_modelo["campos"]:
                campo, _ = ModeloCampo.objects.update_or_create(
                    modelo=modelo,
                    fila=datos_campo["fila"],
                    columna=datos_campo["columna"],
                    defaults={
                        "tipo_valor": datos_campo["tipo_valor"],
                        "orden": datos_campo["orden"],
                        "etiqueta_fila": datos_campo.get("etiqueta_fila", ""),
                        "etiqueta_columna": datos_campo.get("etiqueta_columna", ""),
                    },
                )
                ids_campos_vigentes.append(campo.id)
            modelo.campos.exclude(id__in=ids_campos_vigentes).delete()
            modelos_guardados[numero] = modelo

        for datos_dimension in plan["dimensiones"]:
            dimension, _ = Dimension.objects.update_or_create(
                version=version,
                codigo=datos_dimension["codigo"],
                defaults={
                    "nombre": datos_dimension["nombre"],
                    "orden": int(datos_dimension["codigo"]),
                },
            )
            for datos_indicador in datos_dimension["indicadores"]:
                indicador, _ = Indicador.objects.update_or_create(
                    dimension=dimension,
                    codigo=datos_indicador["codigo"],
                    defaults={"texto": datos_indicador["texto"]},
                )
                for datos_criterio in datos_indicador["criterios"]:
                    criterio, _ = Criterio.objects.update_or_create(
                        indicador=indicador,
                        codigo=datos_criterio["codigo"],
                        defaults={
                            "codigo_manual": datos_criterio["codigo_manual"],
                            "codigo_guia": datos_criterio["codigo_guia"],
                            "solo_en_guia": datos_criterio["solo_en_guia"],
                            "texto": datos_criterio["texto"],
                            "tipo_dato": datos_criterio["tipo_dato"],
                            "valoracion_por_categoria": datos_criterio[
                                "valoracion_por_categoria"
                            ],
                            "nota_normativa": datos_criterio["nota_normativa"],
                        },
                    )
                    criterio.evidencias_sugeridas.all().delete()
                    criterio.requisitos_categoria.all().delete()
                    criterio.modelos_relacionados.all().delete()
                    _crear_evidencias(criterio, datos_criterio["evidencias"])
                    for categoria, texto in datos_criterio["requisitos"]:
                        RequisitoCategoria.objects.create(
                            criterio=criterio,
                            categoria=categoria,
                            texto=texto,
                        )
                    for referencia in datos_criterio["modelos"]:
                        CriterioModelo.objects.create(
                            criterio=criterio,
                            modelo=modelos_guardados[referencia.numero],
                        )

    return {
        "version": version,
        "dimensiones": len(plan["dimensiones"]),
        "indicadores": sum(len(dimension["indicadores"]) for dimension in plan["dimensiones"]),
        "criterios": sum(
            len(indicador["criterios"])
            for dimension in plan["dimensiones"]
            for indicador in dimension["indicadores"]
        ),
        "modelos": len(plan["modelos"]),
        "asociaciones": sum(
            len(criterio["modelos"])
            for dimension in plan["dimensiones"]
            for indicador in dimension["indicadores"]
            for criterio in indicador["criterios"]
        ),
        "campos_modelo": sum(
            len(modelo["campos"])
            for modelo in plan["modelos"].values()
        ),
    }
