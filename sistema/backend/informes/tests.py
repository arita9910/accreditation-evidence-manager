from tempfile import TemporaryDirectory
from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor
from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from .prototipo_docx import crear_prototipo_docx
from .generador import CARACTERES_POR_PAGINA_ESTIMADA, contar_paginas
from .modelos import SECCIONES_INFORME_DOCUMENTADAS, TextoInforme, VersionInforme
from .servicios import guardar_texto, generar_version
from cuentas.modelos import AsignacionParEvaluador, Usuario
from cuentas.permisos import puede
from ciclos.modelos import Carrera, Ciclo, Facultad
from estructura.modelos import VersionNormativa
from nucleo import almacenamiento


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
            self.assertEqual(filas[1].cells[1].text, "Resumen del claustro")
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


class ServiciosInformesTests(TestCase):
    def setUp(self):
        self.facultad = Facultad.objects.create(nombre="Facultad")
        self.carrera = Carrera.objects.create(
            facultad=self.facultad,
            nombre="Carrera",
        )
        self.version_normativa = VersionNormativa.objects.create(
            nombre="SEA-CU 2025",
            fecha_aprobacion=date(2025, 1, 1),
            fuentes="Fuentes",
            activa=True,
        )
        self.ciclo = Ciclo.objects.create(
            carrera=self.carrera,
            version_normativa=self.version_normativa,
            tipo="ordinario",
            anio_base=2026,
            curso_inicial=2021,
            curso_final=2025,
            estado=Ciclo.Estado.ABIERTO,
            fecha_apertura=date(2026, 1, 1),
        )
        self.director = Usuario.objects.create_user(
            "director-informes",
            "Clave-segura-123!",
            nombre="Director",
            apellidos="Carrera",
            email="director-informes@example.com",
            rol=Usuario.Rol.DIRECTOR_CARRERA,
            carrera=self.carrera,
        )
        self.par = Usuario.objects.create_user(
            "par-informes",
            "Clave-segura-123!",
            nombre="Par",
            apellidos="Evaluador",
            email="par-informes@example.com",
            rol=Usuario.Rol.PAR_EVALUADOR,
        )

    def test_par_evaluador_y_asignacion_vigente(self):
        hoy = timezone.localdate()
        asignacion = AsignacionParEvaluador.objects.create(
            usuario=self.par,
            ciclo=self.ciclo,
            vigente_desde=hoy - timedelta(days=1),
            vigente_hasta=hoy + timedelta(days=1),
        )
        self.assertTrue(asignacion.esta_vigente(hoy))
        self.assertTrue(puede(self.par, "consultar_expediente", objeto=self.ciclo))

        asignacion.vigente_hasta = hoy - timedelta(days=2)
        with self.assertRaises(ValidationError):
            asignacion.save()

    def test_guardar_texto_requiere_autorizacion_y_ciclo_abierto(self):
        texto = guardar_texto(
            self.ciclo,
            "caracterizacion",
            "Caracterización de prueba.",
            self.director,
        )
        self.assertEqual(texto.editado_por, self.director)
        self.assertEqual(texto.contenido, "Caracterización de prueba.")

        otro = Usuario.objects.create_user(
            "otro-informes",
            "Clave-segura-123!",
            nombre="Otro",
            apellidos="Usuario",
            email="otro-informes@example.com",
            rol=Usuario.Rol.PAR_EVALUADOR,
        )
        with self.assertRaises(ValidationError):
            guardar_texto(
                self.ciclo,
                "caracterizacion",
                "No autorizado",
                otro,
            )

        self.ciclo.estado = Ciclo.Estado.CERRADO
        self.ciclo.fecha_cierre = timezone.localdate()
        self.ciclo.save()
        with self.assertRaises(ValidationError):
            guardar_texto(
                self.ciclo,
                "estrategia_sostenibilidad",
                "Ciclo cerrado",
                self.director,
            )

    def test_generar_version_incrementa_numero_y_guarda_huella(self):
        texto = guardar_texto(
            self.ciclo,
            "caracterizacion",
            "Contenido breve",
            self.director,
        )
        primera = generar_version(self.ciclo, self.director)
        segunda = generar_version(self.ciclo, self.director)

        self.assertEqual(primera.numero, 1)
        self.assertEqual(segunda.numero, 2)
        self.assertEqual(len(segunda.sha256), 64)
        self.assertEqual(segunda.fichero, segunda.fichero)
        self.assertTrue(almacenamiento.verificar_huella(segunda.fichero, segunda.sha256))
        self.assertIn(segunda.metodo_conteo, {"libreoffice", "estimado"})

    def test_conteo_estimado_declara_metodo_y_constante(self):
        with TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "prueba.docx"
            ruta.write_bytes(b"docx")
            paginas, metodo = contar_paginas(
                ruta,
                "x" * (CARACTERES_POR_PAGINA_ESTIMADA * 51),
            )
        self.assertEqual(paginas, 51)
        self.assertEqual(metodo, "estimado")
