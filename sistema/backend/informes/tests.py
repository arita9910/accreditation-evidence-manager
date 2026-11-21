from tempfile import TemporaryDirectory
from pathlib import Path
from decimal import Decimal
from uuid import uuid4

from django.conf import settings

from docx import Document
from docx.shared import Pt, RGBColor
from datetime import date, timedelta

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from .prototipo_docx import crear_prototipo_docx
from .generador import CARACTERES_POR_PAGINA_ESTIMADA, contar_paginas, generar_docx
from .modelos import SECCIONES_INFORME_DOCUMENTADAS, TextoInforme, VersionInforme
from .servicios import guardar_texto, generar_version
from cuentas.modelos import AsignacionParEvaluador, Usuario
from cuentas.permisos import puede
from ciclos.modelos import Carrera, Ciclo, Facultad
from cuantitativos.models import ValorModelo
from estructura.modelos import (
    Criterio,
    Dimension,
    Indicador,
    ModeloCampo,
    ModeloDefinicion,
    TipoEvidencia,
    VersionNormativa,
)
from evidencias.modelos import Evidencia, FicheroEvidencia
from valoracion.models import Valoracion, ValoracionCriterio, ValoracionEvidencia
from nucleo import almacenamiento
from auditoria.modelos import RegistroAuditoria


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

    def test_generar_docx_incluye_bloque_obligatorio_modelos_estilo_y_porcentaje(self):
        guardar_texto(
            self.ciclo,
            "caracterizacion",
            "Caracterización editable.",
            self.director,
        )
        guardar_texto(
            self.ciclo,
            "plan_mejora",
            "Plan cualitativo.",
            self.director,
        )
        guardar_texto(
            self.ciclo,
            "estrategia_sostenibilidad",
            "Sostenibilidad editable.",
            self.director,
        )

        for numero in range(1, 12):
            modelo = ModeloDefinicion.objects.create(
                version=self.version_normativa,
                numero=numero,
                nombre=f"Modelo de prueba {numero}",
            )
            campo = ModeloCampo.objects.create(
                modelo=modelo,
                fila=1,
                columna=1,
                tipo_valor=(
                    ModeloCampo.TipoValor.PORCENTAJE
                    if numero == 1
                    else ModeloCampo.TipoValor.ENTERO
                ),
                orden=1,
                etiqueta_fila="Indicador",
                etiqueta_columna="Dato",
            )
            ValorModelo.objects.create(
                ciclo=self.ciclo,
                campo=campo,
                curso=2021,
                valor=Decimal("86.3636") if numero == 1 else Decimal("3"),
                numerador=Decimal("19") if numero == 1 else None,
                denominador=Decimal("22") if numero == 1 else None,
            )

        ruta = generar_docx(self.ciclo)
        self.assertTrue(ruta.is_file())

        documento = Document(ruta)
        titulos = [parrafo.text for parrafo in documento.paragraphs]
        for texto in (
            "Informe de autoevaluación",
            "Datos del ciclo",
            "Caracterización",
            "Análisis por dimensión",
            "Plan de mejora",
            "Sostenibilidad",
            "Modelos anexos",
        ):
            self.assertIn(texto, titulos)
        for numero in range(1, 12):
            self.assertTrue(
                any(texto.startswith(f"Modelo {numero}:") for texto in titulos),
            )

        texto_celdas = [
            parrafo.text
            for tabla in documento.tables
            for fila in tabla.rows
            for celda in fila.cells
            for parrafo in celda.paragraphs
        ]
        self.assertIn("86,4 % (19/22)", texto_celdas)
        for encabezado in (
            "MODELO 4. PROYECTOS DE INVESTIGACIÓN",
            "Tipo de proyecto",
            "Modelo 7.1 premios estudiantiles",
            "ESTADÍSTICA DE LOS PREMIOS DEL CLAUSTRO",
            "Excelencia",
            "MODELO 11. RESUMEN PROMOCIÓN, EFICIENCIA, RETENCIÓN",
        ):
            self.assertIn(encabezado, texto_celdas)

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

    def test_generar_docx_incluye_fortalezas_debilidades_criterios_y_evidencias(self):
        dimension = Dimension.objects.create(
            version=self.version_normativa,
            codigo="D1",
            nombre="Dimensión de prueba",
            orden=1,
        )
        indicador = Indicador.objects.create(
            dimension=dimension,
            codigo="I1",
            texto="Indicador de prueba",
        )
        criterio = Criterio.objects.create(
            indicador=indicador,
            codigo="D1-I1-C1",
            codigo_guia="D1-I1-C1-G",
            solo_en_guia=False,
            texto="Criterio de prueba",
            tipo_dato=Criterio.TipoDato.CUALITATIVO,
            valoracion_por_categoria=False,
        )
        tipo_evidencia = TipoEvidencia.objects.create(
            dimension=dimension,
            nombre="Documento",
            naturaleza=TipoEvidencia.Naturaleza.DOCUMENTO,
            soporte_exigido=TipoEvidencia.Soporte.DIGITAL,
        )
        evidencia = Evidencia.objects.create(
            ciclo=self.ciclo,
            tipo_evidencia=tipo_evidencia,
            titulo="Acta de prueba",
            periodo_desde=date(2021, 1, 1),
            periodo_hasta=date(2025, 12, 31),
            soporte=Evidencia.Soporte.DIGITAL,
        )
        fortaleza = Valoracion.objects.create(
            ciclo=self.ciclo,
            dimension=dimension,
            tipo=Valoracion.Tipo.FORTALEZA,
            texto="Fortaleza verificable.",
            redactada_por=self.director,
        )
        debilidad = Valoracion.objects.create(
            ciclo=self.ciclo,
            dimension=dimension,
            tipo=Valoracion.Tipo.DEBILIDAD,
            texto="Debilidad verificable.",
            redactada_por=self.director,
        )
        ValoracionCriterio.objects.create(
            valoracion=fortaleza,
            criterio=criterio,
        )
        ValoracionCriterio.objects.create(
            valoracion=debilidad,
            criterio=criterio,
        )
        ValoracionEvidencia.objects.create(
            valoracion=fortaleza,
            evidencia=evidencia,
        )
        ValoracionEvidencia.objects.create(
            valoracion=debilidad,
            evidencia=evidencia,
        )

        ruta = generar_docx(self.ciclo)
        documento = Document(ruta)
        textos = [parrafo.text for parrafo in documento.paragraphs]
        contenido = "\n".join(textos)

        self.assertIn("Fortaleza verificable.", contenido)
        self.assertIn("Debilidad verificable.", contenido)
        self.assertIn("D1-I1-C1", contenido)
        self.assertIn("Acta de prueba", contenido)


class ApiInformesTests(TestCase):
    def setUp(self):
        facultad = Facultad.objects.create(nombre="Facultad API")
        carrera = Carrera.objects.create(facultad=facultad, nombre="Carrera API")
        version = VersionNormativa.objects.create(
            nombre="SEA-CU API",
            fecha_aprobacion=date(2025, 1, 1),
            fuentes="Fuentes API",
            activa=True,
        )
        self.ciclo = Ciclo.objects.create(
            carrera=carrera,
            version_normativa=version,
            tipo="ordinario",
            anio_base=2026,
            curso_inicial=2021,
            curso_final=2025,
            estado=Ciclo.Estado.ABIERTO,
            fecha_apertura=date(2026, 1, 1),
        )
        self.director = Usuario.objects.create_user(
            "director-api-informes",
            "Clave-segura-123!",
            nombre="Director",
            apellidos="API",
            email="director-api-informes@example.com",
            rol=Usuario.Rol.DIRECTOR_CARRERA,
            carrera=carrera,
        )
        self.par = Usuario.objects.create_user(
            "par-api-informes",
            "Clave-segura-123!",
            nombre="Par",
            apellidos="API",
            email="par-api-informes@example.com",
            rol=Usuario.Rol.PAR_EVALUADOR,
        )

    def test_textos_y_versiones_requieren_permisos_y_registran_expediente(self):
        self.client.force_login(self.director)
        put = self.client.put(
            f"/api/ciclos/{self.ciclo.pk}/informe/textos/caracterizacion/",
            data={"contenido": "Texto desde API"},
            content_type="application/json",
        )
        self.assertEqual(put.status_code, 200)

        lista = self.client.get(
            f"/api/ciclos/{self.ciclo.pk}/informe/textos/"
        )
        self.assertEqual(lista.status_code, 200)

        hoy = timezone.localdate()
        AsignacionParEvaluador.objects.create(
            usuario=self.par,
            ciclo=self.ciclo,
            vigente_desde=hoy - timedelta(days=1),
            vigente_hasta=hoy + timedelta(days=1),
        )
        dimension = Dimension.objects.create(
            version=self.ciclo.version_normativa,
            codigo="D1-API",
            nombre="Dimensión API",
            orden=1,
        )
        tipo = TipoEvidencia.objects.create(
            dimension=dimension,
            nombre="Documento API",
            naturaleza=TipoEvidencia.Naturaleza.DOCUMENTO,
            soporte_exigido=TipoEvidencia.Soporte.DIGITAL,
        )
        evidencia = Evidencia.objects.create(
            ciclo=self.ciclo,
            tipo_evidencia=tipo,
            titulo="Evidencia API",
            periodo_desde=date(2021, 1, 1),
            periodo_hasta=date(2025, 12, 31),
            soporte=Evidencia.Soporte.DIGITAL,
        )
        nombre_interno = uuid4()
        fichero = FicheroEvidencia.objects.create(
            evidencia=evidencia,
            version=1,
            nombre_original="prueba.txt",
            nombre_interno=nombre_interno,
            tamano=4,
            tipo_mime="text/plain",
            sha256="0" * 64,
            vigente=True,
            subido_por=self.director,
        )
        ruta_fichero = (
            Path(settings.EVIDENCIAS_ROOT)
            / "ciclos"
            / str(evidencia.pk)
            / "evidencias"
        )
        ruta_fichero.mkdir(parents=True, exist_ok=True)
        (ruta_fichero / f"{nombre_interno}.txt").write_text(
            "API",
            encoding="utf-8",
        )
        generada = self.client.post(
            f"/api/ciclos/{self.ciclo.pk}/informe/generar/",
        )
        self.assertEqual(generada.status_code, 201)
        version_id = generada.json()["id"]
        self.client.force_login(self.par)
        versiones = self.client.get(
            f"/api/ciclos/{self.ciclo.pk}/informe/versiones/"
        )
        self.assertEqual(versiones.status_code, 200)
        self.assertEqual(
            len(versiones.json()["versiones"]),
            1,
        )
        self.assertEqual(
            versiones.json()["versiones"][0]["id"],
            version_id,
        )

        descarga_informe = self.client.get(
            f"/api/informes/versiones/{version_id}/descarga/"
        )
        self.assertEqual(descarga_informe.status_code, 200)

        expediente = self.client.get(
            f"/api/ciclos/{self.ciclo.pk}/expediente/"
        )
        self.assertEqual(expediente.status_code, 200)
        descarga_expediente = self.client.get(
            f"/api/ciclos/{self.ciclo.pk}/expediente/ficheros/{fichero.pk}/descarga/"
        )
        self.assertEqual(descarga_expediente.status_code, 200)
        self.assertTrue(
            RegistroAuditoria.objects.filter(
                accion="consultar_expediente",
                usuario=self.par,
            ).exists()
        )

    def test_caducidad_impide_expediente_y_usuario_sin_permiso_recibe_403(self):
        hoy = timezone.localdate()
        AsignacionParEvaluador.objects.create(
            usuario=self.par,
            ciclo=self.ciclo,
            vigente_desde=hoy - timedelta(days=3),
            vigente_hasta=hoy - timedelta(days=1),
        )
        self.client.force_login(self.par)
        respuesta = self.client.get(
            f"/api/ciclos/{self.ciclo.pk}/expediente/"
        )
        self.assertEqual(respuesta.status_code, 403)

        otro = Usuario.objects.create_user(
            "otro-api-informes",
            "Clave-segura-123!",
            nombre="Otro",
            apellidos="API",
            email="otro-api-informes@example.com",
            rol=Usuario.Rol.PAR_EVALUADOR,
        )
        self.client.force_login(otro)
        respuesta = self.client.post(
            f"/api/ciclos/{self.ciclo.pk}/informe/generar/",
        )
        self.assertEqual(respuesta.status_code, 403)
