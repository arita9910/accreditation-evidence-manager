import re
import shutil
import subprocess
import tempfile
import unicodedata
from collections import defaultdict
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor

from .modelos import TextoInforme
from cuantitativos.models import ValorModelo
from estructura.models import Dimension, ModeloDefinicion
from mejora.modelos import AccionMejora
from valoracion.models import Valoracion
from valoracion.servicios import formatear_porcentaje


CARACTERES_POR_PAGINA_ESTIMADA = 1800


def _numero_para_relacion(valor):
    if valor is None:
        return ""
    texto = format(valor, "f").rstrip("0").rstrip(".")
    return texto or "0"


def _nombre_usuario(usuario):
    nombre = " ".join(
        parte.strip()
        for parte in (getattr(usuario, "nombre", ""), getattr(usuario, "apellidos", ""))
        if parte and parte.strip()
    )
    return nombre or usuario.get_username()


def _normalizar_etiqueta(texto):
    if texto is None:
        return ""
    base = unicodedata.normalize("NFKD", str(texto))
    sin_tildes = "".join(caracter for caracter in base if not unicodedata.combining(caracter))
    return re.sub(r"\s+", " ", sin_tildes).strip().lower()


def _formatear_valor_modelo(valor, campo):
    if campo.tipo_valor == campo.TipoValor.PORCENTAJE:
        if valor.numerador is not None and valor.denominador is not None:
            return formatear_porcentaje(
                _numero_para_relacion(valor.numerador),
                _numero_para_relacion(valor.denominador),
            )
        if valor.valor is not None:
            return f"{valor.valor} %"
        return "Sin dato"
    if valor.valor is not None:
        return str(valor.valor)
    return "Sin dato"


def _construir_datos_modelo(valores_modelo):
    por_clave = {}
    pendientes = []
    for valor in valores_modelo:
        clave = (
            _normalizar_etiqueta(valor.campo.etiqueta_fila),
            _normalizar_etiqueta(valor.campo.etiqueta_columna),
        )
        texto_valor = _formatear_valor_modelo(valor, valor.campo)
        if clave not in por_clave or por_clave[clave] in {"", "Sin dato"}:
            por_clave[clave] = texto_valor
        pendientes.append(texto_valor)
    return {"por_clave": por_clave, "pendientes": pendientes}


def _valor_modelo(datos_modelo, etiqueta_fila, etiqueta_columna, defecto="Sin dato"):
    clave = (_normalizar_etiqueta(etiqueta_fila), _normalizar_etiqueta(etiqueta_columna))
    if clave in datos_modelo["por_clave"]:
        return datos_modelo["por_clave"][clave]
    if datos_modelo["pendientes"]:
        return datos_modelo["pendientes"].pop(0)
    return defecto


def _agregar_modelo_1(documento, datos_modelo):
    tabla = documento.add_table(rows=8, cols=5)
    tabla.style = "Table Grid"
    tabla.cell(0, 0).merge(tabla.cell(0, 4)).text = "MODELO 1. RESUMEN DEL CLAUSTRO"
    tabla.cell(1, 1).text = "Acreditación anterior"
    tabla.cell(1, 2).text = "%"
    tabla.cell(1, 3).text = "Acreditación actual"
    tabla.cell(1, 4).text = "%"
    filas = [
        "Total del claustro",
        "Doctores en ciencias",
        "Doctores en ciencias y equivalentes",
        "Doctores en ciencias en especialidades afines",
        "Máster en ciencias del resto del claustro",
        "Profesores titulares y auxiliares",
    ]
    columnas = ("Acreditación anterior", "%", "Acreditación actual", "%")
    for indice, fila_etiqueta in enumerate(filas, start=2):
        tabla.cell(indice, 0).text = fila_etiqueta
        for columna_indice, columna_etiqueta in enumerate(columnas, start=1):
            tabla.cell(indice, columna_indice).text = _valor_modelo(
                datos_modelo,
                fila_etiqueta,
                columna_etiqueta,
            )


def _agregar_modelo_2(documento, datos_modelo):
    tabla = documento.add_table(rows=15, cols=8)
    tabla.style = "Table Grid"
    tabla.cell(0, 0).merge(tabla.cell(0, 7)).text = "MODELO 2. PUBLICACIONES"
    encabezados = ("CLASIFICACIÓN", "5", "4", "3", "2", "1", "TOTAL", "")
    for indice, encabezado in enumerate(encabezados):
        tabla.cell(1, indice).text = encabezado
    filas = [
        "Artículo grupo I",
        "Artículo grupo II",
        "Artículo grupo III",
        "Artículo grupo IV",
        "Artículo sin grupo",
        "Libro",
        "Capítulo de libro",
        "Patentes",
        "Texto de la carrera",
        "Materiales Docente interno",
        "Grupos 1 al 4, libros y patentes",
        "Grupos 1 y 2",
        "TOTAL",
    ]
    columnas = ("5", "4", "3", "2", "1", "TOTAL")
    for fila_indice, fila_etiqueta in enumerate(filas, start=2):
        tabla.cell(fila_indice, 0).text = fila_etiqueta
        for col_indice, col_etiqueta in enumerate(columnas, start=1):
            tabla.cell(fila_indice, col_indice).text = _valor_modelo(
                datos_modelo,
                fila_etiqueta,
                col_etiqueta,
            )
    tabla.cell(11, 7).text = "ÍNDICES"


def _agregar_modelo_3(documento, datos_modelo):
    tabla = documento.add_table(rows=10, cols=8)
    tabla.style = "Table Grid"
    tabla.cell(0, 0).merge(tabla.cell(0, 7)).text = "MODELO 3. PRESENTACIÓN DE PONENCIAS EN EVENTOS"
    encabezados = ("CLASIFICACIÓN", "-5", "-4", "-3", "-2", "-1", "TOTAL", "")
    for indice, encabezado in enumerate(encabezados):
        tabla.cell(1, indice).text = encabezado
    filas = [
        "Internacional",
        "Nacional",
        "Provincial",
        "Municipal",
        "De base",
        "Provincial, nacional e internacional",
        "TOTAL",
    ]
    columnas = ("-5", "-4", "-3", "-2", "-1", "TOTAL")
    for fila_indice, fila_etiqueta in enumerate(filas, start=2):
        tabla.cell(fila_indice, 0).text = fila_etiqueta
        for col_indice, col_etiqueta in enumerate(columnas, start=1):
            tabla.cell(fila_indice, col_indice).text = _valor_modelo(
                datos_modelo,
                fila_etiqueta,
                col_etiqueta,
            )
    tabla.cell(6, 7).text = "ÍNDICES"


def _agregar_modelo_4(documento, datos_modelo):
    tabla = documento.add_table(rows=4, cols=10)
    tabla.style = "Table Grid"
    tabla.cell(0, 0).merge(tabla.cell(0, 9)).text = "MODELO 4. PROYECTOS DE INVESTIGACIÓN"

    tabla.cell(1, 0).text = "No."
    tabla.cell(1, 1).text = "Proyecto"
    tabla.cell(1, 2).text = "Tipo de proyecto"
    tabla.cell(1, 2).merge(tabla.cell(1, 4))
    tabla.cell(1, 5).text = "Profesor que participa"
    tabla.cell(1, 6).text = "Plazo de realización"
    tabla.cell(1, 6).merge(tabla.cell(1, 7))
    tabla.cell(1, 8).text = "Nivel particip."
    tabla.cell(1, 8).merge(tabla.cell(1, 9))

    tabla.cell(1, 0).merge(tabla.cell(2, 0))
    tabla.cell(1, 1).merge(tabla.cell(2, 1))
    tabla.cell(1, 5).merge(tabla.cell(2, 5))
    tabla.cell(2, 2).text = "PAP"
    tabla.cell(2, 3).text = "PNAP"
    tabla.cell(2, 4).text = "P. Internacional"
    tabla.cell(2, 6).text = "Desde"
    tabla.cell(2, 7).text = "Hasta"
    tabla.cell(2, 8).text = "J de Proyecto"
    tabla.cell(2, 9).text = "Investigador"

    tabla.cell(3, 0).text = _valor_modelo(datos_modelo, "Proyecto", "No.")
    tabla.cell(3, 1).text = _valor_modelo(datos_modelo, "Proyecto de investigación", "Proyecto")
    tabla.cell(3, 2).text = _valor_modelo(datos_modelo, "Tipo de proyecto", "PAP")
    tabla.cell(3, 3).text = _valor_modelo(datos_modelo, "Tipo de proyecto", "PNAP")
    tabla.cell(3, 4).text = _valor_modelo(datos_modelo, "Tipo de proyecto", "P. Internacional")
    tabla.cell(3, 5).text = _valor_modelo(datos_modelo, "Profesor que participa", "Profesor que participa")
    tabla.cell(3, 6).text = _valor_modelo(datos_modelo, "Plazo de realización", "Desde")
    tabla.cell(3, 7).text = _valor_modelo(datos_modelo, "Plazo de realización", "Hasta")
    tabla.cell(3, 8).text = _valor_modelo(datos_modelo, "Nivel de participación", "J de Proyecto")
    tabla.cell(3, 9).text = _valor_modelo(datos_modelo, "Nivel de participación", "Investigador")


def _agregar_modelo_5(documento, datos_modelo):
    tabla = documento.add_table(rows=14, cols=4)
    tabla.style = "Table Grid"
    tabla.cell(0, 0).merge(tabla.cell(0, 3)).text = "MODELO 5. INCORPORACIÓN A PROYECTOS DE INVESTIGACIÓN"

    tabla.cell(1, 0).text = "Proyectos de investigación del claustro"
    tabla.cell(1, 0).merge(tabla.cell(5, 0))
    tabla.cell(1, 2).text = "CLASIFICACIÓN"
    tabla.cell(1, 3).text = "CANTIDAD"
    clasificaciones = ("PAP", "PNAP", "Internacionales", "TOTAL")
    for indice, clasificacion in enumerate(clasificaciones, start=2):
        tabla.cell(indice, 2).text = clasificacion
        tabla.cell(indice, 3).text = _valor_modelo(
            datos_modelo,
            "Proyectos de investigación del claustro",
            clasificacion,
        )

    tabla.cell(6, 0).text = "Estudiantes investigando"
    tabla.cell(6, 0).merge(tabla.cell(12, 0))
    tabla.cell(6, 1).text = "AÑO"
    tabla.cell(6, 2).text = "CANTIDAD"
    tabla.cell(6, 3).text = "%"
    anos = ("1", "2", "3", "4", "…n", "TOTAL")
    for indice, ano in enumerate(anos, start=7):
        tabla.cell(indice, 1).text = ano
        tabla.cell(indice, 2).text = _valor_modelo(datos_modelo, "Estudiantes investigando", ano)
        tabla.cell(indice, 3).text = _valor_modelo(datos_modelo, "Estudiantes investigando", "%", defecto="")

    tabla.cell(13, 0).text = "Profesores incorporados"
    tabla.cell(13, 1).merge(tabla.cell(13, 3)).text = _valor_modelo(
        datos_modelo,
        "Profesores incorporados",
        "Profesores incorporados",
        defecto="",
    )


def _agregar_modelo_6(documento, datos_modelo):
    tabla = documento.add_table(rows=16, cols=5)
    tabla.style = "Table Grid"
    tabla.cell(0, 0).merge(tabla.cell(0, 4)).text = "MODELO 6. INCORPORACIÓN A PROYECTOS COMUNITARIOS Y EXTENSIONISTAS"

    tabla.cell(1, 0).text = "Proyectos"
    tabla.cell(1, 0).merge(tabla.cell(7, 0))
    tabla.cell(1, 2).text = "NOMENCLATURA DEL PROYECTO"
    tabla.cell(1, 4).text = "CANTIDAD"
    clasificaciones = ("Comunitario", "Extensionista", "Educativo", "Cultural", "Deportivo", "TOTAL")
    for indice, clasificacion in enumerate(clasificaciones, start=2):
        tabla.cell(indice, 2).text = clasificacion
        tabla.cell(indice, 4).text = _valor_modelo(datos_modelo, "Proyectos", clasificacion)

    tabla.cell(8, 0).text = "Estudiantes incorporados"
    tabla.cell(8, 0).merge(tabla.cell(14, 0))
    tabla.cell(8, 1).text = "AÑO"
    tabla.cell(8, 2).text = "CANTIDAD"
    tabla.cell(8, 4).text = "%"
    anos = ("1", "2", "3", "4", "5", "6", "TOTAL")
    for indice, ano in enumerate(anos, start=9):
        tabla.cell(indice, 1).text = ano
        tabla.cell(indice, 2).text = _valor_modelo(datos_modelo, "Estudiantes incorporados", ano)
        tabla.cell(indice, 4).text = _valor_modelo(datos_modelo, "Estudiantes incorporados", "%", defecto="")

    tabla.cell(15, 0).text = "Profesores incorporados"
    tabla.cell(15, 1).merge(tabla.cell(15, 4)).text = _valor_modelo(
        datos_modelo,
        "Profesores incorporados",
        "Profesores incorporados",
        defecto="",
    )


def _agregar_modelo_7(documento, datos_modelo):
    tabla = documento.add_table(rows=40, cols=8)
    tabla.style = "Table Grid"
    tabla.cell(0, 0).merge(tabla.cell(0, 7)).text = "MODELO 7. RESUMEN DE LOS PREMIOS OBTENIDOS"
    tabla.cell(1, 0).merge(tabla.cell(1, 7)).text = "PREMIOS DEL CLAUSTRO"
    encabezados = ("Premio", "5", "4", "3", "2", "1", "0", "TOTAL")
    for indice, encabezado in enumerate(encabezados):
        tabla.cell(2, indice).text = encabezado

    filas_claustro = [
        "Premio nacional de la ACC",
        "Premio provincial de la ACC",
        "Premio nacional CITMA",
        "Premio provincial CITMA",
        "Premio BTJ",
        "Sello forjadores el futuro",
        "Premio del rector",
        "Distinción del ministro",
        "Relevante del fórum nacional de ciencia y técnica",
        "Destacado del fórum nacional de ciencia y técnica",
        "Mención del fórum nacional de ciencia y técnica",
        "Relevante del fórum provincial de ciencia y técnica",
        "Destacado del fórum provincial de ciencia y técnica",
        "Mención del fórum provincial de ciencia y técnica",
        "Relevante del fórum municipal de ciencia y técnica",
        "Destacado del fórum municipal de ciencia y técnica",
        "Mención del fórum municipal de ciencia y técnica",
        "Otro (describir)",
        "Otro (describir)",
        "Otro (describir)",
        "Total",
    ]
    columnas = ("5", "4", "3", "2", "1", "0", "TOTAL")
    fila_base = 3
    for desplazamiento, fila_etiqueta in enumerate(filas_claustro):
        fila_tabla = fila_base + desplazamiento
        tabla.cell(fila_tabla, 0).text = fila_etiqueta
        for col_indice, col_etiqueta in enumerate(columnas, start=1):
            tabla.cell(fila_tabla, col_indice).text = _valor_modelo(datos_modelo, fila_etiqueta, col_etiqueta)

    inicio_71 = fila_base + len(filas_claustro)
    tabla.cell(inicio_71, 0).merge(tabla.cell(inicio_71, 7)).text = "Modelo 7.1 premios estudiantiles"
    for indice, encabezado in enumerate(encabezados):
        tabla.cell(inicio_71 + 1, indice).text = encabezado

    filas_estudiantiles = [
        "Destacado fórum nacional de estudiantes",
        "Relevante fórum nacional de estudiantes",
        "Mención fórum nacional de estudiantes",
        "Premio jornada científica estudiantil de facultad",
        "Relevantes fórum de CES",
        "Destacados fórum CES",
        "Fórum de historia provincial",
        "Fórum de historia nacional",
        "Concursos nacionales",
        "Concursos internacionales",
        "Otro (describir)",
        "Otro (describir)",
        "TOTAL",
        "TOTAL DE PREMIOS",
    ]
    for desplazamiento, fila_etiqueta in enumerate(filas_estudiantiles):
        fila_tabla = inicio_71 + 2 + desplazamiento
        tabla.cell(fila_tabla, 0).text = fila_etiqueta
        for col_indice, col_etiqueta in enumerate(columnas, start=1):
            tabla.cell(fila_tabla, col_indice).text = _valor_modelo(datos_modelo, fila_etiqueta, col_etiqueta)

    estadisticas = documento.add_table(rows=8, cols=3)
    estadisticas.style = "Table Grid"
    estadisticas.cell(0, 0).text = "ESTADÍSTICA DE LOS PREMIOS DEL CLAUSTRO"
    estadisticas.cell(0, 1).text = "TOTAL"
    estadisticas.cell(0, 2).text = "%"
    filas_estadisticas = [
        "PROFESORES CON PREMIOS CIENTÍFICOS",
        "PROFESORES CON PREMIOS MES E INSTITUCIÓN",
        "PROFESORES CON CONDECORACIONES",
        "PROFESORES CON PREMIOS ESTUDIANTILES",
        "PROFESORES CON OTROS PREMIOS",
        "PROFESORES SIN PREMIOS",
        "TOTAL DE PROFESORES CON PREMIOS",
    ]
    for indice, fila_etiqueta in enumerate(filas_estadisticas, start=1):
        estadisticas.cell(indice, 0).text = fila_etiqueta
        estadisticas.cell(indice, 1).text = _valor_modelo(datos_modelo, fila_etiqueta, "TOTAL")
        estadisticas.cell(indice, 2).text = _valor_modelo(datos_modelo, fila_etiqueta, "%", defecto="")


def _agregar_modelo_8(documento, datos_modelo):
    tabla = documento.add_table(rows=9, cols=8)
    tabla.style = "Table Grid"
    tabla.cell(0, 0).merge(tabla.cell(0, 7)).text = "MODELO 8. ACTIVIDAD DE POSTGRADO"
    encabezados = ("TIPO DE ACTIVIDAD", "-5", "-4", "-3", "-2", "-1", "0", "TOTAL")
    for indice, encabezado in enumerate(encabezados):
        tabla.cell(1, indice).text = encabezado
    filas = (
        "Cursos de postgrado",
        "Diplomado",
        "Especialidades",
        "Maestrías",
        "Doctorados",
        "TOTAL",
    )
    columnas = ("-5", "-4", "-3", "-2", "-1", "0", "TOTAL")
    for indice_fila, fila_etiqueta in enumerate(filas, start=2):
        tabla.cell(indice_fila, 0).text = fila_etiqueta
        for indice_columna, columna_etiqueta in enumerate(columnas, start=1):
            tabla.cell(indice_fila, indice_columna).text = _valor_modelo(
                datos_modelo,
                fila_etiqueta,
                columna_etiqueta,
            )


def _agregar_modelo_9(documento, datos_modelo):
    tabla = documento.add_table(rows=13, cols=7)
    tabla.style = "Table Grid"
    tabla.cell(0, 0).merge(tabla.cell(0, 6)).text = "MODELO 9. POSTGRADOS Y ACREDITACIÓN"
    tabla.cell(1, 2).text = "Excelencia"
    tabla.cell(1, 3).text = "Certificado"
    tabla.cell(1, 4).text = "Avalado"
    tabla.cell(1, 5).text = "Autorizado"
    tabla.cell(1, 6).text = "Total"

    pares = [
        ("Diplomado", 2),
        ("Especialidad", 4),
        ("Maestría", 6),
        ("Doctorado", 8),
        ("Total", 10),
    ]
    for tipo, fila in pares:
        tabla.cell(fila, 0).text = tipo
        tabla.cell(fila, 0).merge(tabla.cell(fila + 1, 0))
        tabla.cell(fila, 1).text = "Propio"
        tabla.cell(fila + 1, 1).text = "Afin"
        for indice_columna, columna in enumerate(("Excelencia", "Certificado", "Avalado", "Autorizado", "Total"), start=2):
            tabla.cell(fila, indice_columna).text = _valor_modelo(datos_modelo, tipo, columna)
            tabla.cell(fila + 1, indice_columna).text = _valor_modelo(
                datos_modelo,
                f"{tipo} Afin",
                columna,
                defecto="",
            )

    tabla.cell(12, 1).text = "Absoluto"
    for indice_columna, columna in enumerate(("Excelencia", "Certificado", "Avalado", "Autorizado", "Total"), start=2):
        tabla.cell(12, indice_columna).text = _valor_modelo(datos_modelo, "Total Absoluto", columna, defecto="")


def _agregar_modelo_10(documento, datos_modelo):
    tabla = documento.add_table(rows=9, cols=9)
    tabla.style = "Table Grid"
    tabla.cell(0, 0).merge(tabla.cell(0, 8)).text = "MODELO 10. RESULTADOS DE LOS EJERCICIOS INTEGRADORES"
    tabla.cell(1, 0).text = "Años"
    tabla.cell(1, 1).text = "Cantidad de Evaluados"
    tabla.cell(1, 2).text = "Calificaciones"
    tabla.cell(1, 2).merge(tabla.cell(1, 5))
    tabla.cell(1, 6).text = "%"
    tabla.cell(1, 7).text = "%"
    tabla.cell(1, 8).text = "%"
    tabla.cell(2, 2).text = "2"
    tabla.cell(2, 3).text = "3"
    tabla.cell(2, 4).text = "4"
    tabla.cell(2, 5).text = "5"
    tabla.cell(2, 6).text = "Aprobados"
    tabla.cell(2, 7).text = "Con 4 ó 5"
    tabla.cell(2, 8).text = "Evaluados"
    tabla.cell(1, 0).merge(tabla.cell(2, 0))
    tabla.cell(1, 1).merge(tabla.cell(2, 1))

    filas = ("2do. Año", "3er. Año", "4to. Año", "5to. Año", "6to. Año", "Total")
    columnas = ("Cantidad de evaluados", "2", "3", "4", "5", "Aprobados", "Con 4 ó 5", "Evaluados")
    for indice, fila_etiqueta in enumerate(filas, start=3):
        tabla.cell(indice, 0).text = fila_etiqueta
        for indice_columna, columna_etiqueta in enumerate(columnas, start=1):
            tabla.cell(indice, indice_columna).text = _valor_modelo(datos_modelo, fila_etiqueta, columna_etiqueta)


def _agregar_modelo_11(documento, datos_modelo):
    tabla = documento.add_table(rows=8, cols=7)
    tabla.style = "Table Grid"
    tabla.cell(0, 0).merge(tabla.cell(0, 6)).text = "MODELO 11. RESUMEN PROMOCIÓN, EFICIENCIA, RETENCIÓN"
    encabezados = ("INDICADORES", "-5", "-4", "-3", "-2", "-1", "0 - 0")
    for indice, encabezado in enumerate(encabezados):
        tabla.cell(1, indice).text = encabezado
    filas = (
        "Promoción",
        "Retención",
        "Eficiencia vertical",
        "Eficiencia académica",
        "Eficiencia ciclo",
    )
    columnas = ("-5", "-4", "-3", "-2", "-1", "0 - 0")
    for indice_fila, fila_etiqueta in enumerate(filas, start=2):
        tabla.cell(indice_fila, 0).text = fila_etiqueta
        for indice_columna, columna_etiqueta in enumerate(columnas, start=1):
            tabla.cell(indice_fila, indice_columna).text = _valor_modelo(
                datos_modelo,
                fila_etiqueta,
                columna_etiqueta,
            )


RENDER_MODELOS = {
    1: _agregar_modelo_1,
    2: _agregar_modelo_2,
    3: _agregar_modelo_3,
    4: _agregar_modelo_4,
    5: _agregar_modelo_5,
    6: _agregar_modelo_6,
    7: _agregar_modelo_7,
    8: _agregar_modelo_8,
    9: _agregar_modelo_9,
    10: _agregar_modelo_10,
    11: _agregar_modelo_11,
}


def contar_paginas(ruta, contenido_cuerpo=None):
    ruta = Path(ruta)
    ejecutable = shutil.which("soffice") or shutil.which("libreoffice")
    if ejecutable:
        with tempfile.TemporaryDirectory() as temporal:
            resultado = subprocess.run(
                [
                    ejecutable,
                    "--headless",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    temporal,
                    str(ruta),
                ],
                capture_output=True,
                check=False,
                timeout=120,
            )
            pdf = next(Path(temporal).glob("*.pdf"), None)
            if resultado.returncode == 0 and pdf is not None:
                datos = pdf.read_bytes()
                coincidencias = re.findall(rb"/Type\s*/Page\b", datos)
                if coincidencias:
                    return len(coincidencias), "libreoffice"

    texto = ""
    if contenido_cuerpo is not None:
        texto = str(contenido_cuerpo)
    elif ruta.exists():
        try:
            documento = Document(ruta)
            texto = "\n".join(parrafo.text for parrafo in documento.paragraphs)
        except Exception:
            texto = ""
    caracteres = len(texto.strip())
    paginas = max(1, (caracteres + CARACTERES_POR_PAGINA_ESTIMADA - 1) // CARACTERES_POR_PAGINA_ESTIMADA)
    return paginas, "estimado"


def generar_docx(ciclo) -> Path:
    documento = Document()
    documento.add_heading("Informe de autoevaluación", level=0)

    documento.add_heading("Datos del ciclo", level=1)
    documento.add_paragraph(f"Carrera: {ciclo.carrera.nombre}")
    documento.add_paragraph(f"Tipo: {ciclo.tipo}")
    documento.add_paragraph(f"Período académico: {ciclo.curso_inicial}-{ciclo.curso_final}")
    documento.add_paragraph(f"Año base: {ciclo.anio_base}")
    documento.add_paragraph(f"Estado: {ciclo.get_estado_display()}")
    if ciclo.categoria_obtenida:
        documento.add_paragraph(f"Categoría obtenida: {ciclo.categoria_obtenida}")

    textos = {
        texto.seccion: texto.contenido
        for texto in TextoInforme.objects.filter(ciclo=ciclo)
    }

    documento.add_heading("Caracterización", level=1)
    documento.add_paragraph(textos.get("caracterizacion", "").strip() or "Sin caracterización registrada.")

    documento.add_heading("Análisis por dimensión", level=1)
    dimensiones = Dimension.objects.filter(version=ciclo.version_normativa).order_by("orden", "pk")
    for dimension in dimensiones:
        documento.add_heading(str(dimension), level=2)
        valoraciones = (
            Valoracion.objects.filter(ciclo=ciclo, dimension=dimension)
            .select_related("dimension", "redactada_por")
            .prefetch_related("criterios__criterio", "evidencias__evidencia")
            .order_by("tipo", "pk")
        )
        documento.add_heading("Fortalezas", level=3)
        fortalezas = [valoracion for valoracion in valoraciones if valoracion.tipo == Valoracion.Tipo.FORTALEZA]
        if fortalezas:
            for valoracion in fortalezas:
                documento.add_paragraph(valoracion.texto, style="List Bullet")
                criterios = [relacion.criterio for relacion in valoracion.criterios.all()]
                evidencias = [relacion.evidencia for relacion in valoracion.evidencias.all()]
                if criterios:
                    documento.add_paragraph(
                        "Criterios: " + ", ".join(criterio.codigo for criterio in criterios)
                    )
                if evidencias:
                    documento.add_paragraph(
                        "Evidencias: " + "; ".join(evidencia.titulo for evidencia in evidencias)
                    )
        else:
            documento.add_paragraph("Sin fortalezas registradas.")

        documento.add_heading("Debilidades", level=3)
        debilidades = [valoracion for valoracion in valoraciones if valoracion.tipo == Valoracion.Tipo.DEBILIDAD]
        if debilidades:
            for valoracion in debilidades:
                documento.add_paragraph(valoracion.texto, style="List Bullet")
                criterios = [relacion.criterio for relacion in valoracion.criterios.all()]
                evidencias = [relacion.evidencia for relacion in valoracion.evidencias.all()]
                if criterios:
                    documento.add_paragraph(
                        "Criterios: " + ", ".join(criterio.codigo for criterio in criterios)
                    )
                if evidencias:
                    documento.add_paragraph(
                        "Evidencias: " + "; ".join(evidencia.titulo for evidencia in evidencias)
                    )
        else:
            documento.add_paragraph("Sin debilidades registradas.")

    documento.add_heading("Plan de mejora", level=1)
    documento.add_paragraph(textos.get("plan_mejora", "").strip() or "Sin texto cualitativo del plan de mejora.")

    plan = getattr(ciclo, "plan_mejora", None)
    if plan is not None:
        documento.add_paragraph(f"Estado del plan: {plan.get_estado_display()}")
        acciones = AccionMejora.objects.filter(plan=plan).select_related(
            "debilidad", "responsable"
        ).order_by("pk")
        if acciones:
            tabla = documento.add_table(rows=1, cols=6)
            tabla.style = "Table Grid"
            encabezados = (
                "Descripción",
                "Responsable",
                "Fecha límite",
                "Estado",
                "Resultado",
                "Debilidad",
            )
            for celda, encabezado in zip(tabla.rows[0].cells, encabezados):
                celda.text = encabezado
            for accion in acciones:
                responsable = _nombre_usuario(accion.responsable)
                fila = tabla.add_row().cells
                fila[0].text = accion.descripcion
                fila[1].text = responsable
                fila[2].text = accion.fecha_limite.isoformat()
                fila[3].text = accion.get_estado_display()
                fila[4].text = accion.valoracion_resultado or ""
                fila[5].text = accion.debilidad.texto
        else:
            documento.add_paragraph("Sin acciones de mejora registradas.")

    documento.add_heading("Sostenibilidad", level=1)
    documento.add_paragraph(
        textos.get("estrategia_sostenibilidad", "").strip()
        or "Sin estrategia de sostenibilidad registrada."
    )

    ciclo_anterior = getattr(ciclo, "ciclo_anterior", None)
    if ciclo_anterior is not None:
        documento.add_heading("Plan del ciclo anterior valorado", level=1)
        documento.add_paragraph(
            f"Ciclo anterior: {ciclo_anterior.carrera.nombre} "
            f"({ciclo_anterior.curso_inicial}-{ciclo_anterior.curso_final})"
        )
        plan_anterior = getattr(ciclo_anterior, "plan_mejora", None)
        if plan_anterior is None:
            documento.add_paragraph("No existe un plan de mejora registrado para el ciclo anterior.")
        else:
            documento.add_paragraph(f"Estado del plan: {plan_anterior.get_estado_display()}")
            acciones = AccionMejora.objects.filter(plan=plan_anterior).select_related(
                "debilidad", "responsable"
            ).order_by("pk")
            if acciones:
                tabla = documento.add_table(rows=1, cols=5)
                tabla.style = "Table Grid"
                for celda, encabezado in zip(
                    tabla.rows[0].cells,
                    ("Acción", "Responsable", "Fecha límite", "Estado", "Valoración del resultado"),
                ):
                    celda.text = encabezado
                for accion in acciones:
                    responsable = _nombre_usuario(accion.responsable)
                    fila = tabla.add_row().cells
                    fila[0].text = accion.descripcion
                    fila[1].text = responsable
                    fila[2].text = accion.fecha_limite.isoformat()
                    fila[3].text = accion.get_estado_display()
                    fila[4].text = accion.valoracion_resultado or ""
            else:
                documento.add_paragraph("Sin acciones registradas en el plan anterior.")

    documento.add_heading("Modelos anexos", level=1)
    modelos = list(
        ModeloDefinicion.objects.filter(version=ciclo.version_normativa)
        .prefetch_related("campos")
        .order_by("numero", "pk")
    )
    modelos_por_numero = {modelo.numero: modelo for modelo in modelos}
    valores = list(
        ValorModelo.objects.filter(ciclo=ciclo)
        .select_related("campo", "campo__modelo")
        .order_by("campo__modelo__numero", "campo__orden", "curso", "campo__fila", "campo__columna")
    )
    valores_por_modelo = defaultdict(list)
    for valor in valores:
        valores_por_modelo[valor.campo.modelo.numero].append(valor)

    for numero in range(1, 12):
        modelo = modelos_por_numero.get(numero)
        nombre = modelo.nombre if modelo is not None else "Datos no registrados"
        documento.add_heading(f"Modelo {numero}: {nombre}", level=2)
        if modelo is None:
            documento.add_paragraph("Sin definición y datos registrados.")
            continue

        campos = list(modelo.campos.all().order_by("fila", "columna", "orden", "pk"))
        if not campos:
            documento.add_paragraph("Sin campos registrados.")
            continue
        render_modelo = RENDER_MODELOS.get(numero)
        if render_modelo is None:
            documento.add_paragraph("Sin plantilla visual definida.")
            continue
        datos_modelo = _construir_datos_modelo(valores_por_modelo.get(numero, []))
        render_modelo(documento, datos_modelo)

    documento.styles["Normal"].font.name = "Arial"
    documento.styles["Normal"].font.size = Pt(12)
    documento.styles["Normal"].font.color.rgb = RGBColor(0, 0, 0)
    for parrafo in documento.paragraphs:
        parrafo.paragraph_format.line_spacing = 1.0
        for run in parrafo.runs:
            run.font.name = "Arial"
            run.font.size = Pt(12)
            run.font.color.rgb = RGBColor(0, 0, 0)
    for tabla in documento.tables:
        for fila in tabla.rows:
            for celda in fila.cells:
                for parrafo in celda.paragraphs:
                    parrafo.paragraph_format.line_spacing = 1.0
                    for run in parrafo.runs:
                        run.font.name = "Arial"
                        run.font.size = Pt(12)
                        run.font.color.rgb = RGBColor(0, 0, 0)

    ruta = Path(__file__).with_name(f"version_ciclo_{ciclo.pk}.docx")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    documento.save(ruta)
    return ruta


__all__ = ["CARACTERES_POR_PAGINA_ESTIMADA", "contar_paginas", "generar_docx"]
