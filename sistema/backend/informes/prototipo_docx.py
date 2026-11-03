import argparse
import json
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.shared import Pt, RGBColor


MODELOS_RESUMEN = (
    Path(__file__).resolve().parents[2] / "datos" / "modelos_resumen.json"
)


def crear_prototipo_docx(ruta_salida: str | Path | None = None) -> Path:
    with MODELOS_RESUMEN.open(encoding="utf-8") as archivo:
        modelos = json.load(archivo)["modelos"]

    modelo = next(modelo for modelo in modelos if modelo["codigo"] == "M1")
    nombre = modelo["nombre"]["valor"] or "Pendiente"
    criterios = ", ".join(modelo["criterios_referenciados"]["valores"])

    documento = Document()
    documento.add_paragraph("Prototipo de modelo resumen")
    tabla = documento.add_table(rows=1, cols=3)
    tabla.style = "Table Grid"
    encabezados = tabla.rows[0].cells
    encabezados[0].text = "Modelo"
    encabezados[1].text = "Nombre"
    encabezados[2].text = "Criterios"
    celdas = tabla.add_row().cells
    celdas[0].text = modelo["codigo"]
    celdas[1].text = nombre
    celdas[2].text = criterios

    documento.add_paragraph("Datos del modelo resumen.")
    documento.add_section(WD_SECTION.CONTINUOUS)

    documento.styles["Normal"].font.name = "Arial"
    documento.styles["Normal"].font.size = Pt(12)
    documento.styles["Normal"].font.color.rgb = RGBColor(0, 0, 0)
    parrafos = list(documento.paragraphs)
    parrafos.extend(
        parrafo
        for fila in tabla.rows
        for celda in fila.cells
        for parrafo in celda.paragraphs
    )
    for parrafo in parrafos:
        parrafo.paragraph_format.line_spacing = 1.0
        for run in parrafo.runs:
            run.font.name = "Arial"
            run.font.size = Pt(12)
            run.font.color.rgb = RGBColor(0, 0, 0)

    if ruta_salida is None:
        ruta_salida = Path(__file__).with_name("prototipo.docx")
    destino = Path(ruta_salida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    documento.save(destino)
    return destino


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera un DOCX de prueba para el modelo resumen M1."
    )
    parser.add_argument(
        "salida",
        nargs="?",
        help="Ruta de salida (por defecto, prototipo.docx junto al script).",
    )
    argumentos = parser.parse_args()
    print(crear_prototipo_docx(argumentos.salida))


if __name__ == "__main__":
    main()
