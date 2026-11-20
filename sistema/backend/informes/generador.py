import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor

from .modelos import TextoInforme


CARACTERES_POR_PAGINA_ESTIMADA = 1800


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
    documento.add_heading("Informe de autoevaluación", level=1)
    documento.add_heading("Datos del ciclo", level=2)
    documento.add_paragraph(f"Carrera: {ciclo.carrera.nombre}")
    documento.add_paragraph(f"Tipo: {ciclo.tipo}")
    documento.add_paragraph(f"Período: {ciclo.curso_inicial}-{ciclo.curso_final}")

    for texto in TextoInforme.objects.filter(ciclo=ciclo).order_by("seccion"):
        documento.add_heading(texto.seccion.replace("_", " ").title(), level=2)
        documento.add_paragraph(texto.contenido or "")

    documento.styles["Normal"].font.name = "Arial"
    documento.styles["Normal"].font.size = Pt(12)
    documento.styles["Normal"].font.color.rgb = RGBColor(0, 0, 0)
    for parrafo in documento.paragraphs:
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
