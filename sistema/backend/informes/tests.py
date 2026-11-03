from tempfile import TemporaryDirectory
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor
from django.test import SimpleTestCase

from .prototipo_docx import crear_prototipo_docx


class PrototipoDocxTests(SimpleTestCase):
    def test_creates_formatted_model_table_and_section_break(self):
        with TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "prototipo.docx"
            resultado = crear_prototipo_docx(ruta)

            self.assertEqual(resultado, ruta)
            self.assertTrue(ruta.is_file())

            documento = Document(ruta)
            self.assertEqual(
                documento.paragraphs[0].text,
                "Prototipo de modelo resumen",
            )
            self.assertEqual(
                documento.paragraphs[1].text,
                "Datos del modelo resumen.",
            )
            self.assertEqual(len(documento.tables), 1)
            filas = documento.tables[0].rows
            self.assertEqual(filas[1].cells[0].text, "M1")
            self.assertEqual(filas[1].cells[1].text, "Pendiente")
            self.assertEqual(filas[1].cells[2].text, "2.2.1, 2.2.3")
            self.assertEqual(len(documento.sections), 2)

            parrafos = list(documento.paragraphs)
            parrafos.extend(
                parrafo
                for tabla in documento.tables
                for fila in tabla.rows
                for celda in fila.cells
                for parrafo in celda.paragraphs
            )
            for parrafo in parrafos:
                self.assertEqual(parrafo.paragraph_format.line_spacing, 1.0)
                for run in parrafo.runs:
                    self.assertEqual(run.font.name, "Arial")
                    self.assertEqual(run.font.size, Pt(12))
                    self.assertEqual(run.font.color.rgb, RGBColor(0, 0, 0))
