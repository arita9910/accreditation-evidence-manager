import hashlib
from datetime import date
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase

from ciclos.modelos import Carrera, Ciclo, Facultad
from cuentas.permisos import puede
from estructura.models import Criterio, Dimension, Indicador, TipoEvidencia, VersionNormativa

from .modelos import Clasificacion, Evidencia, FicheroEvidencia
from .servicios import (
    TAMANO_MAXIMO_BYTES,
    crear_evidencia,
    descargar,
    reemplazar_fichero,
    verificar_huella,
    verificar_huellas,
)


class EvidenciasModelosTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            "usuario-evidencia",
            "clave-segura-123",
            nombre="Usuario",
            apellidos="Prueba",
            email="usuario@example.com",
        )
        self.facultad = Facultad.objects.create(nombre="Ingeniería")
        self.carrera = Carrera.objects.create(
            facultad=self.facultad,
            nombre="Ingeniería Informática",
            activa=True,
        )
        self.version = VersionNormativa.objects.create(
            nombre="SEA-CU 2025",
            fecha_aprobacion=date(2025, 1, 1),
            fuentes="Fuente",
            activa=True,
        )
        self.dimension = Dimension.objects.create(
            version=self.version,
            codigo="1",
            nombre="Pertinencia",
            orden=1,
        )
        self.indicador = Indicador.objects.create(
            dimension=self.dimension,
            codigo="I1",
            texto="Indicador de prueba",
        )
        self.criterio = Criterio.objects.create(
            indicador=self.indicador,
            codigo="C1",
            codigo_guia="C-1",
            solo_en_guia=False,
            texto="Criterio de prueba",
            tipo_dato=Criterio.TipoDato.CUALITATIVO,
            valoracion_por_categoria=False,
        )
        self.tipo_evidencia = TipoEvidencia.objects.create(
            dimension=self.dimension,
            nombre="Documento de soporte",
            naturaleza=TipoEvidencia.Naturaleza.DOCUMENTO,
            soporte_exigido=TipoEvidencia.Soporte.DIGITAL,
        )
        self.ciclo = Ciclo.objects.create(
            carrera=self.carrera,
            version_normativa=self.version,
            tipo="ordinario",
            anio_base=2026,
            curso_inicial=2021,
            curso_final=2025,
            estado=Ciclo.Estado.ABIERTO,
            fecha_apertura=date(2026, 1, 1),
        )

    def test_evidencia_crea_relaciones_y_fichero_vigente_unico(self):
        evidencia = Evidencia.objects.create(
            ciclo=self.ciclo,
            tipo_evidencia=self.tipo_evidencia,
            titulo="Memoria de autoevaluación",
            descripcion="Documento principal del ciclo",
            curso_academico=2025,
            periodo_desde=date(2025, 9, 1),
            periodo_hasta=date(2026, 6, 30),
            soporte=Evidencia.Soporte.DIGITAL,
        )
        FicheroEvidencia.objects.create(
            evidencia=evidencia,
            version=1,
            nombre_original="memoria.pdf",
            nombre_interno="f0f2123d-9f07-4210-a9f4-fce7995b1d38",
            tamano=128,
            tipo_mime="application/pdf",
            sha256="a" * 64,
            vigente=True,
            subido_por=self.usuario,
        )
        otro = FicheroEvidencia(
            evidencia=evidencia,
            version=2,
            nombre_original="memoria-v2.pdf",
            nombre_interno="2eb0ba4b-babe-4a0d-90c6-4ea69471e8e0",
            tamano=140,
            tipo_mime="application/pdf",
            sha256="b" * 64,
            vigente=True,
            subido_por=self.usuario,
        )

        with self.assertRaises(ValidationError):
            otro.full_clean()

        Clasificacion.objects.create(
            evidencia=evidencia,
            criterio=self.criterio,
            clasificada_por=self.usuario,
        )

        self.assertEqual(evidencia.ficheros.count(), 1)
        self.assertEqual(evidencia.clasificaciones.count(), 1)

    def test_evidencia_acepta_curso_academico_en_formato_texto_y_vacio(self):
        evidencia = Evidencia.objects.create(
            ciclo=self.ciclo,
            tipo_evidencia=self.tipo_evidencia,
            titulo="Evidencia con curso textual",
            descripcion="Curso académico con guion",
            curso_academico="2024-2025",
            periodo_desde=date(2024, 9, 1),
            periodo_hasta=date(2025, 7, 31),
            soporte=Evidencia.Soporte.DIGITAL,
        )
        self.assertEqual(evidencia.curso_academico, "2024-2025")

        opcional = Evidencia.objects.create(
            ciclo=self.ciclo,
            tipo_evidencia=self.tipo_evidencia,
            titulo="Evidencia opcional",
            descripcion="Sin curso académico",
            curso_academico="",
            periodo_desde=date(2025, 9, 1),
            periodo_hasta=date(2026, 7, 31),
            soporte=Evidencia.Soporte.DIGITAL,
        )
        self.assertEqual(opcional.curso_academico, "")

    def test_evidencia_en_papel_exige_custodia_y_no_admite_archivo(self):
        evidencia = Evidencia(
            ciclo=self.ciclo,
            tipo_evidencia=self.tipo_evidencia,
            titulo="Evidencia en papel",
            descripcion="Documento oficial",
            curso_academico=2025,
            periodo_desde=date(2025, 9, 1),
            periodo_hasta=date(2026, 6, 30),
            soporte=Evidencia.Soporte.PAPEL,
        )

        with self.assertRaises(ValidationError):
            evidencia.full_clean()

        evidencia.custodia_original = "Caja fuerte 1"
        evidencia.full_clean()
        evidencia.save()

        fichero = FicheroEvidencia(
            evidencia=evidencia,
            version=1,
            nombre_original="documento.pdf",
            nombre_interno="9bfdd1fa-e6e5-4e0f-af0f-a5d6d5d766b7",
            tamano=90,
            tipo_mime="application/pdf",
            sha256="c" * 64,
            vigente=True,
            subido_por=self.usuario,
        )

        with self.assertRaises(ValidationError):
            fichero.full_clean()

    def test_ciclo_cerrado_rechaza_evidencia_y_clasificacion(self):
        ciclo_cerrado = Ciclo.objects.create(
            carrera=self.carrera,
            version_normativa=self.version,
            tipo="ordinario",
            anio_base=2027,
            curso_inicial=2022,
            curso_final=2026,
            estado=Ciclo.Estado.CERRADO,
            fecha_apertura=date(2027, 1, 1),
            fecha_cierre=date(2027, 12, 1),
        )

        evidencia = Evidencia(
            ciclo=ciclo_cerrado,
            tipo_evidencia=self.tipo_evidencia,
            titulo="Evidencia fuera de plazo",
            descripcion="No debe permitirse",
            curso_academico=2026,
            periodo_desde=date(2026, 1, 1),
            periodo_hasta=date(2026, 12, 31),
            soporte=Evidencia.Soporte.DIGITAL,
        )

        with self.assertRaises(ValidationError):
            evidencia.full_clean()

        clasificacion = Clasificacion(
            evidencia=Evidencia.objects.create(
                ciclo=self.ciclo,
                tipo_evidencia=self.tipo_evidencia,
                titulo="Evidencia de prueba",
                descripcion="Desc",
                curso_academico=2025,
                periodo_desde=date(2025, 9, 1),
                periodo_hasta=date(2026, 6, 30),
                soporte=Evidencia.Soporte.DIGITAL,
            ),
            criterio=self.criterio,
            clasificada_por=self.usuario,
        )
        clasificacion.evidencia.ciclo = ciclo_cerrado
        with self.assertRaises(ValidationError):
            clasificacion.full_clean()

    def test_clasificacion_rechaza_criterio_de_otra_version(self):
        otra_version = VersionNormativa.objects.create(
            nombre="Otra versión",
            fecha_aprobacion=date(2024, 1, 1),
            fuentes="Fuente",
            activa=True,
        )
        otra_dimension = Dimension.objects.create(
            version=otra_version,
            codigo="2",
            nombre="Otro nivel",
            orden=2,
        )
        otro_indicador = Indicador.objects.create(
            dimension=otra_dimension,
            codigo="I2",
            texto="Indicador ajeno",
        )
        otro_criterio = Criterio.objects.create(
            indicador=otro_indicador,
            codigo="C2",
            codigo_guia="C-2",
            solo_en_guia=False,
            texto="Criterio de otra versión",
            tipo_dato=Criterio.TipoDato.CUALITATIVO,
            valoracion_por_categoria=False,
        )

        clasificacion = Clasificacion(
            evidencia=Evidencia.objects.create(
                ciclo=self.ciclo,
                tipo_evidencia=self.tipo_evidencia,
                titulo="Evidencia",
                descripcion="de prueba",
                curso_academico=2025,
                periodo_desde=date(2025, 1, 1),
                periodo_hasta=date(2025, 12, 31),
                soporte=Evidencia.Soporte.DIGITAL,
            ),
            criterio=otro_criterio,
            clasificada_por=self.usuario,
        )

        with self.assertRaises(ValidationError):
            clasificacion.full_clean()


class EvidenciasServiciosTests(TestCase):
    def setUp(self):
        self.facultad = Facultad.objects.create(nombre="Ingeniería")
        self.carrera = Carrera.objects.create(
            facultad=self.facultad,
            nombre="Ingeniería Informática",
            activa=True,
        )
        self.version = VersionNormativa.objects.create(
            nombre="SEA-CU 2025",
            fecha_aprobacion=date(2025, 1, 1),
            fuentes="Fuente",
            activa=True,
        )
        self.dimension = Dimension.objects.create(
            version=self.version,
            codigo="1",
            nombre="Pertinencia",
            orden=1,
        )
        self.indicador = Indicador.objects.create(
            dimension=self.dimension,
            codigo="I1",
            texto="Indicador",
        )
        self.criterio = Criterio.objects.create(
            indicador=self.indicador,
            codigo="C1",
            codigo_guia="C-1",
            solo_en_guia=False,
            texto="Criterio",
            tipo_dato=Criterio.TipoDato.CUALITATIVO,
            valoracion_por_categoria=False,
        )
        self.tipo_evidencia = TipoEvidencia.objects.create(
            dimension=self.dimension,
            nombre="Documento de soporte",
            naturaleza=TipoEvidencia.Naturaleza.DOCUMENTO,
            soporte_exigido=TipoEvidencia.Soporte.DIGITAL,
        )
        self.usuario = get_user_model().objects.create_user(
            "usuario-servicios",
            "clave-segura-123",
            nombre="Usuario",
            apellidos="Servicios",
            email="servicios@example.com",
            carrera=self.carrera,
            rol="director_carrera",
        )
        self.ciclo = Ciclo.objects.create(
            carrera=self.carrera,
            version_normativa=self.version,
            tipo="ordinario",
            anio_base=2026,
            curso_inicial=2021,
            curso_final=2025,
            estado=Ciclo.Estado.ABIERTO,
            fecha_apertura=date(2026, 1, 1),
        )

    def test_crear_evidencia_guarda_archivo_y_audita(self):
        archivo = SimpleUploadedFile("memoria.pdf", b"contenido pdf", content_type="application/pdf")
        evidencia = crear_evidencia(
            self.ciclo,
            {
                "titulo": "Memoria",
                "tipo_evidencia": self.tipo_evidencia,
                "soporte": Evidencia.Soporte.DIGITAL,
                "curso_academico": 2025,
                "periodo_desde": date(2025, 9, 1),
                "periodo_hasta": date(2026, 6, 30),
                "descripcion": "Documentación principal",
            },
            archivo=archivo,
            usuario=self.usuario,
        )

        self.assertEqual(evidencia.ficheros.count(), 1)
        fichero = evidencia.ficheros.get()
        self.assertTrue(fichero.vigente)
        self.assertEqual(fichero.subido_por, self.usuario)
        self.assertEqual(verificar_huella(fichero), "correcta")

    def test_reemplazar_fichero_crea_version_nueva_y_conserva_historial(self):
        primera = SimpleUploadedFile("memoria.pdf", b"contenido viejo", content_type="application/pdf")
        evidencia = crear_evidencia(
            self.ciclo,
            {
                "titulo": "Memoria",
                "tipo_evidencia": self.tipo_evidencia,
                "soporte": Evidencia.Soporte.DIGITAL,
                "curso_academico": 2025,
                "periodo_desde": date(2025, 9, 1),
                "periodo_hasta": date(2026, 6, 30),
            },
            archivo=primera,
            usuario=self.usuario,
        )

        segunda = SimpleUploadedFile("memoria.pdf", b"contenido nuevo", content_type="application/pdf")
        nuevo = reemplazar_fichero(evidencia, segunda, usuario=self.usuario)

        self.assertEqual(evidencia.ficheros.count(), 2)
        self.assertEqual(evidencia.ficheros.filter(vigente=True).count(), 1)
        self.assertEqual(nuevo.version, 2)
        self.assertFalse(evidencia.ficheros.get(version=1).vigente)
        self.assertEqual(verificar_huella(nuevo), "correcta")

    def test_verificar_huellas_detecta_archivo_alterado(self):
        archivo = SimpleUploadedFile("archivo.pdf", b"contenido original", content_type="application/pdf")
        evidencia = crear_evidencia(
            self.ciclo,
            {
                "titulo": "Archivo",
                "tipo_evidencia": self.tipo_evidencia,
                "soporte": Evidencia.Soporte.DIGITAL,
                "curso_academico": 2025,
                "periodo_desde": date(2025, 9, 1),
                "periodo_hasta": date(2026, 6, 30),
            },
            archivo=archivo,
            usuario=self.usuario,
        )
        fichero = evidencia.ficheros.get()

        resumen = verificar_huellas(self.ciclo)
        self.assertEqual(resumen["total"], 1)
        self.assertEqual(resumen["correctas"], 1)
        self.assertEqual(resumen["alteradas"], 0)

        ruta = Path(settings.EVIDENCIAS_ROOT) / "ciclos" / str(evidencia.pk) / "evidencias" / f"{fichero.nombre_interno}{Path(fichero.nombre_original).suffix}"
        ruta.write_bytes(b"contenido modificado")

        self.assertEqual(verificar_huella(fichero), "alterada")
        resumen_dos = verificar_huellas(self.ciclo)
        self.assertEqual(resumen_dos["alteradas"], 1)

    def test_descargar_rechaza_usuario_no_autorizado_y_permite_una_descarga(self):
        archivo = SimpleUploadedFile("archivo.pdf", b"contenido descarga", content_type="application/pdf")
        evidencia = crear_evidencia(
            self.ciclo,
            {
                "titulo": "Descarga",
                "tipo_evidencia": self.tipo_evidencia,
                "soporte": Evidencia.Soporte.DIGITAL,
                "curso_academico": 2025,
                "periodo_desde": date(2025, 9, 1),
                "periodo_hasta": date(2026, 6, 30),
            },
            archivo=archivo,
            usuario=self.usuario,
        )
        fichero = evidencia.ficheros.get()

        respuesta = descargar(fichero, usuario=self.usuario)
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("attachment; filename=\"archivo.pdf\"", respuesta["Content-Disposition"])

        with self.assertRaises(Exception):
            descargar(fichero, usuario=AnonymousUser())

    def test_crear_evidencia_rechaza_archivo_mayor_a_10mb(self):
        archivo = SimpleUploadedFile(
            "grande.pdf",
            b"a" * (TAMANO_MAXIMO_BYTES + 1),
            content_type="application/pdf",
        )
        with self.assertRaises(ValidationError) as contexto:
            crear_evidencia(
                self.ciclo,
                {
                    "titulo": "Archivo grande",
                    "tipo_evidencia": self.tipo_evidencia,
                    "soporte": Evidencia.Soporte.DIGITAL,
                    "curso_academico": 2025,
                    "periodo_desde": date(2025, 9, 1),
                    "periodo_hasta": date(2026, 6, 30),
                },
                archivo=archivo,
                usuario=self.usuario,
            )
        self.assertIn("10 MB", str(contexto.exception))


class EvidenciasApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.facultad = Facultad.objects.create(nombre="Ingeniería")
        cls.carrera = Carrera.objects.create(
            facultad=cls.facultad,
            nombre="Ingeniería Informática",
            activa=True,
        )
        cls.otra_carrera = Carrera.objects.create(
            facultad=cls.facultad,
            nombre="Ingeniería de Telecomunicaciones",
            activa=True,
        )
        cls.version = VersionNormativa.objects.create(
            nombre="SEA-CU 2025",
            fecha_aprobacion=date(2025, 1, 1),
            fuentes="Fuente",
            activa=True,
        )
        cls.dimension = Dimension.objects.create(
            version=cls.version,
            codigo="1",
            nombre="Pertinencia",
            orden=1,
        )
        cls.indicador = Indicador.objects.create(
            dimension=cls.dimension,
            codigo="I1",
            texto="Indicador de prueba",
        )
        cls.criterio = Criterio.objects.create(
            indicador=cls.indicador,
            codigo="C1",
            codigo_guia="C-1",
            solo_en_guia=False,
            texto="Criterio de prueba",
            tipo_dato=Criterio.TipoDato.CUALITATIVO,
            valoracion_por_categoria=False,
        )
        cls.tipo_evidencia = TipoEvidencia.objects.create(
            dimension=cls.dimension,
            nombre="Documento de soporte",
            naturaleza=TipoEvidencia.Naturaleza.DOCUMENTO,
            soporte_exigido=TipoEvidencia.Soporte.DIGITAL,
        )
        cls.director = get_user_model().objects.create_user(
            "director-evidencias",
            "clave-segura-123",
            nombre="Director",
            apellidos="Carrera",
            email="director@example.com",
            rol=get_user_model()._meta.get_field("rol").choices[1][0],
            carrera=cls.carrera,
        )
        cls.otro_director = get_user_model().objects.create_user(
            "director-otra-carrera",
            "clave-segura-123",
            nombre="Otro",
            apellidos="Director",
            email="otro-director@example.com",
            rol=get_user_model()._meta.get_field("rol").choices[1][0],
            carrera=cls.otra_carrera,
        )
        cls.ciclo = Ciclo.objects.create(
            carrera=cls.carrera,
            version_normativa=cls.version,
            tipo="ordinario",
            anio_base=2026,
            curso_inicial=2021,
            curso_final=2025,
            estado=Ciclo.Estado.ABIERTO,
            fecha_apertura=date(2026, 1, 1),
        )

    def _crear_evidencia(self, *, titulo="Memoria de autoevaluación"):
        archivo = SimpleUploadedFile("memoria.pdf", b"contenido pdf", content_type="application/pdf")
        response = self.client.post(
            "/api/evidencias/",
            {
                "ciclo": self.ciclo.pk,
                "tipo_evidencia": self.tipo_evidencia.pk,
                "titulo": titulo,
                "descripcion": "Documento principal del ciclo",
                "curso_academico": 2025,
                "periodo_desde": "2025-09-01",
                "periodo_hasta": "2026-06-30",
                "soporte": "digital",
                "archivo": archivo,
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 201, response.content)
        return response.json()

    def test_listado_y_detalle_de_evidencias(self):
        self.client.force_login(self.director)
        evidencia = Evidencia.objects.create(
            ciclo=self.ciclo,
            tipo_evidencia=self.tipo_evidencia,
            titulo="Listado de evidencias",
            descripcion="Prueba de listado",
            curso_academico=2025,
            periodo_desde=date(2025, 9, 1),
            periodo_hasta=date(2026, 6, 30),
            soporte=Evidencia.Soporte.DIGITAL,
        )
        FicheroEvidencia.objects.create(
            evidencia=evidencia,
            version=1,
            nombre_original="listado.pdf",
            nombre_interno="d7d01c0e-bd1c-4d6b-8c24-0c8d5d508dd0",
            tamano=100,
            tipo_mime="application/pdf",
            sha256="d" * 64,
            vigente=True,
            subido_por=self.director,
        )

        response = self.client.get("/api/evidencias/")
        self.assertEqual(response.status_code, 200)
        resultados = response.json()["results"]
        self.assertTrue(any(item["id"] == evidencia.pk for item in resultados))

        detalle = self.client.get(f"/api/evidencias/{evidencia.pk}/")
        self.assertEqual(detalle.status_code, 200)
        self.assertEqual(detalle.json()["titulo"], "Listado de evidencias")

    def test_listado_ignora_filtros_fk_con_formato_invalido(self):
        self.client.force_login(self.director)
        Evidencia.objects.create(
            ciclo=self.ciclo,
            tipo_evidencia=self.tipo_evidencia,
            titulo="Evidencia filtro inválido",
            descripcion="Prueba",
            curso_academico=2025,
            periodo_desde=date(2025, 9, 1),
            periodo_hasta=date(2026, 6, 30),
            soporte=Evidencia.Soporte.DIGITAL,
        )
        response = self.client.get("/api/evidencias/?dimension=1&criterio=1.1.1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [])

    def test_creacion_acepta_fichero_y_rechaza_validacion(self):
        self.client.force_login(self.director)

        response = self._crear_evidencia(titulo="Evidencia creada por API")
        self.assertEqual(response["titulo"], "Evidencia creada por API")
        self.assertEqual(Evidencia.objects.filter(titulo="Evidencia creada por API").count(), 1)

        bad_response = self.client.post(
            "/api/evidencias/",
            {
                "ciclo": self.ciclo.pk,
                "tipo_evidencia": self.tipo_evidencia.pk,
                "titulo": "",
                "descripcion": "Sin título",
                "curso_academico": 2025,
                "periodo_desde": "2025-09-01",
                "periodo_hasta": "2026-06-30",
                "soporte": "digital",
            },
            content_type="application/json",
        )
        self.assertEqual(bad_response.status_code, 400)

    def test_descarga_y_verificacion_huella_respetan_permisos(self):
        self.client.force_login(self.director)
        evidencia = Evidencia.objects.create(
            ciclo=self.ciclo,
            tipo_evidencia=self.tipo_evidencia,
            titulo="Evidencia para descargar",
            descripcion="Descarga",
            curso_academico=2025,
            periodo_desde=date(2025, 9, 1),
            periodo_hasta=date(2026, 6, 30),
            soporte=Evidencia.Soporte.DIGITAL,
        )
        contenido = b"contenido descarga"
        fichero = FicheroEvidencia.objects.create(
            evidencia=evidencia,
            version=1,
            nombre_original="descarga.pdf",
            nombre_interno="a0f9d2d2-9715-4f67-a2a3-61d44534b8c3",
            tamano=len(contenido),
            tipo_mime="application/pdf",
            sha256=hashlib.sha256(contenido).hexdigest(),
            vigente=True,
            subido_por=self.director,
        )
        archivo = Path(settings.EVIDENCIAS_ROOT) / "ciclos" / str(evidencia.pk) / "evidencias" / f"{fichero.nombre_interno}.pdf"
        archivo.parent.mkdir(parents=True, exist_ok=True)
        archivo.write_bytes(contenido)

        self.assertTrue(puede(self.director, "descargar_evidencia", objeto=evidencia))
        self.assertFalse(puede(self.otro_director, "descargar_evidencia", objeto=evidencia))

        response = self.client.get(f"/api/ficheros/{fichero.pk}/descarga/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("attachment; filename=\"descarga.pdf\"", response["Content-Disposition"])

        self.client.force_login(self.otro_director)
        denied = self.client.get(f"/api/ficheros/{fichero.pk}/descarga/")
        self.assertEqual(denied.status_code, 403)

        self.client.force_login(self.director)
        verify = self.client.post(f"/api/ciclos/{self.ciclo.pk}/verificar-huellas/")
        self.assertEqual(verify.status_code, 200)
        self.assertEqual(verify.json()["total"], 1)
        self.assertEqual(verify.json()["correctas"], 1)

    def test_historial_de_ficheros_y_clasificacion_con_permisos(self):
        self.client.force_login(self.director)
        evidencia = Evidencia.objects.create(
            ciclo=self.ciclo,
            tipo_evidencia=self.tipo_evidencia,
            titulo="Evidencia con historial",
            descripcion="Historial",
            curso_academico=2025,
            periodo_desde=date(2025, 9, 1),
            periodo_hasta=date(2026, 6, 30),
            soporte=Evidencia.Soporte.DIGITAL,
        )
        primer = FicheroEvidencia.objects.create(
            evidencia=evidencia,
            version=1,
            nombre_original="v1.pdf",
            nombre_interno="4cbf7d52-6e37-46b3-aa1c-c1d72d53f0c1",
            tamano=100,
            tipo_mime="application/pdf",
            sha256="f" * 64,
            vigente=True,
            subido_por=self.director,
        )
        archivo = Path(settings.EVIDENCIAS_ROOT) / "ciclos" / str(evidencia.pk) / "evidencias" / f"{primer.nombre_interno}.pdf"
        archivo.parent.mkdir(parents=True, exist_ok=True)
        archivo.write_bytes(b"primera version")

        nueva = SimpleUploadedFile("v2.pdf", b"segunda version", content_type="application/pdf")
        upload = self.client.post(
            f"/api/evidencias/{evidencia.pk}/ficheros/",
            {"archivo": nueva},
            format="multipart",
        )
        self.assertEqual(upload.status_code, 201, upload.content)
        self.assertEqual(len(upload.json()["sha256"]) , 64)
        self.assertTrue(upload.json()["vigente"])

        detalle = self.client.get(f"/api/evidencias/{evidencia.pk}/")
        self.assertEqual(detalle.status_code, 200)
        self.assertEqual(len(detalle.json()["ficheros"]), 2)
        self.assertTrue(all(item["vigente"] is False for item in detalle.json()["ficheros"] if item["version"] == 1))

        self.assertTrue(puede(self.director, "crear_evidencia", objeto=evidencia))
        self.assertFalse(puede(self.otro_director, "crear_evidencia", objeto=evidencia))

        clasificacion = self.client.post(
            f"/api/evidencias/{evidencia.pk}/clasificaciones/",
            {"criterio": self.criterio.pk},
            content_type="application/json",
        )
        self.assertEqual(clasificacion.status_code, 201)
        self.assertEqual(clasificacion.json()["criterio"], self.criterio.pk)

        self.client.force_login(self.otro_director)
        denied = self.client.post(
            f"/api/evidencias/{evidencia.pk}/clasificaciones/",
            {"criterio": self.criterio.pk},
            content_type="application/json",
        )
        self.assertEqual(denied.status_code, 403)

        self.client.force_login(self.director)
        response = self.client.delete(
            f"/api/evidencias/{evidencia.pk}/clasificaciones/",
            {"criterio": self.criterio.pk},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 204)

        criterio_response = self.client.get(f"/api/criterios/{self.criterio.codigo}/evidencias/")
        self.assertEqual(criterio_response.status_code, 200)

    def test_lista_tipos_evidencia_devuelve_catalogo(self):
        self.client.force_login(self.director)
        response = self.client.get("/api/tipos-evidencia/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(item["id"] == self.tipo_evidencia.pk for item in response.json()["results"]))

    def test_creacion_en_papel_sin_archivo_se_permite_y_digital_lo_exige(self):
        self.client.force_login(self.director)

        papel = self.client.post(
            "/api/evidencias/",
            {
                "ciclo": self.ciclo.pk,
                "tipo_evidencia": self.tipo_evidencia.pk,
                "titulo": "Acta impresa",
                "descripcion": "Acta con firma original",
                "curso_academico": 2025,
                "periodo_desde": "2025-09-01",
                "periodo_hasta": "2026-06-30",
                "soporte": "papel",
                "custodia_original": "Secretaría docente",
            },
            format="multipart",
        )
        self.assertEqual(papel.status_code, 201, papel.content)
        self.assertEqual(papel.json()["soporte"], "papel")

        digital_sin_archivo = self.client.post(
            "/api/evidencias/",
            {
                "ciclo": self.ciclo.pk,
                "tipo_evidencia": self.tipo_evidencia.pk,
                "titulo": "Informe sin archivo",
                "descripcion": "Debe fallar",
                "curso_academico": 2025,
                "periodo_desde": "2025-09-01",
                "periodo_hasta": "2026-06-30",
                "soporte": "digital",
            },
            format="multipart",
        )
        self.assertEqual(digital_sin_archivo.status_code, 400)
