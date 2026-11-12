from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from auditoria.modelos import RegistroAuditoria
from ciclos.modelos import AsignacionDimension, Carrera, Ciclo, Facultad
from cuentas.modelos import Usuario
from estructura.models import Criterio, Dimension, Indicador, TipoEvidencia, VersionNormativa
from evidencias.modelos import Evidencia

from .models import Valoracion, ValoracionCriterio, ValoracionEvidencia
from .servicios import (
    crear_valoracion,
    editar_valoracion,
    eliminar_valoracion,
    formatear_porcentaje,
)


class ValoracionModelosTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            "usuario-valoracion",
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
        self.otra_dimension = Dimension.objects.create(
            version=self.version,
            codigo="2",
            nombre="Recursos",
            orden=2,
        )
        self.indicador = Indicador.objects.create(
            dimension=self.dimension,
            codigo="1.1",
            texto="Indicador de prueba",
        )
        self.criterio = Criterio.objects.create(
            indicador=self.indicador,
            codigo="1.1.1",
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
        self.evidencia = Evidencia.objects.create(
            ciclo=self.ciclo,
            tipo_evidencia=self.tipo_evidencia,
            titulo="Memoria de autoevaluación",
            descripcion="Documento principal del ciclo",
            curso_academico=2025,
            periodo_desde=date(2025, 9, 1),
            periodo_hasta=date(2026, 6, 30),
            soporte=Evidencia.Soporte.DIGITAL,
        )
        self.valoracion = Valoracion.objects.create(
            ciclo=self.ciclo,
            dimension=self.dimension,
            tipo=Valoracion.Tipo.FORTALEZA,
            texto="La propuesta tiene un enfoque sólido.",
            redactada_por=self.usuario,
        )

    def test_valoracion_acepta_criterios_y_evidencias_del_mismo_ciclo_y_dimension(self):
        ValoracionCriterio.objects.create(
            valoracion=self.valoracion,
            criterio=self.criterio,
        )
        ValoracionEvidencia.objects.create(
            valoracion=self.valoracion,
            evidencia=self.evidencia,
        )

        self.assertEqual(self.valoracion.criterios.count(), 1)
        self.assertEqual(self.valoracion.evidencias.count(), 1)

    def test_criterio_de_otra_dimension_rechaza_relacion(self):
        otro_criterio = Criterio.objects.create(
            indicador=Indicador.objects.create(
                dimension=self.otra_dimension,
                codigo="2.1",
                texto="Indicador ajeno",
            ),
            codigo="2.1.1",
            codigo_guia="C-2",
            solo_en_guia=False,
            texto="Criterio ajeno",
            tipo_dato=Criterio.TipoDato.CUALITATIVO,
            valoracion_por_categoria=False,
        )

        rel = ValoracionCriterio(valoracion=self.valoracion, criterio=otro_criterio)

        with self.assertRaises(ValidationError):
            rel.full_clean()

    def test_evidencia_de_otro_ciclo_rechaza_relacion(self):
        otra_carrera = Carrera.objects.create(
            facultad=self.facultad,
            nombre="Arquitectura",
            activa=True,
        )
        otro_ciclo = Ciclo.objects.create(
            carrera=otra_carrera,
            version_normativa=self.version,
            tipo="ordinario",
            anio_base=2027,
            curso_inicial=2022,
            curso_final=2026,
            estado=Ciclo.Estado.ABIERTO,
            fecha_apertura=date(2027, 1, 1),
        )
        otra_evidencia = Evidencia.objects.create(
            ciclo=otro_ciclo,
            tipo_evidencia=self.tipo_evidencia,
            titulo="Evidencia ajena",
            descripcion="No debe asociarse a este ciclo",
            curso_academico=2026,
            periodo_desde=date(2026, 9, 1),
            periodo_hasta=date(2027, 6, 30),
            soporte=Evidencia.Soporte.DIGITAL,
        )

        rel = ValoracionEvidencia(valoracion=self.valoracion, evidencia=otra_evidencia)

        with self.assertRaises(ValidationError):
            rel.full_clean()

    def test_ciclo_cerrado_rechaza_valoracion(self):
        ciclo_cerrado = Ciclo.objects.create(
            carrera=self.carrera,
            version_normativa=self.version,
            tipo="ordinario",
            anio_base=2028,
            curso_inicial=2023,
            curso_final=2027,
            estado=Ciclo.Estado.CERRADO,
            fecha_apertura=date(2028, 1, 1),
            fecha_cierre=date(2028, 12, 1),
        )
        valoracion = Valoracion(
            ciclo=ciclo_cerrado,
            dimension=self.dimension,
            tipo=Valoracion.Tipo.DEBILIDAD,
            texto="No debería poder crearse.",
            redactada_por=self.usuario,
        )

        with self.assertRaises(ValidationError):
            valoracion.full_clean()

    def test_tablas_de_union_rechazan_registros_duplicados(self):
        ValoracionCriterio.objects.create(
            valoracion=self.valoracion,
            criterio=self.criterio,
        )
        ValoracionEvidencia.objects.create(
            valoracion=self.valoracion,
            evidencia=self.evidencia,
        )

        with self.assertRaises(ValidationError):
            ValoracionCriterio(
                valoracion=self.valoracion,
                criterio=self.criterio,
            ).full_clean()

        with self.assertRaises(ValidationError):
            ValoracionEvidencia(
                valoracion=self.valoracion,
                evidencia=self.evidencia,
            ).full_clean()


class ValoracionServiciosTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            "miembro-valoracion",
            "clave-segura-123",
            nombre="Miembro",
            apellidos="Prueba",
            email="miembro@example.com",
        )
        self.facultad = Facultad.objects.create(nombre="Ingeniería")
        self.carrera = Carrera.objects.create(
            facultad=self.facultad,
            nombre="Ingeniería Informática",
            activa=True,
        )
        self.otra_carrera = Carrera.objects.create(
            facultad=self.facultad,
            nombre="Arquitectura",
            activa=True,
        )
        self.director = get_user_model().objects.create_user(
            "director-valoracion",
            "clave-segura-123",
            nombre="Director",
            apellidos="Prueba",
            email="director@example.com",
            rol=Usuario.Rol.DIRECTOR_CARRERA,
            carrera=self.carrera,
        )
        self.otro_usuario = get_user_model().objects.create_user(
            "otro-usuario",
            "clave-segura-123",
            nombre="Otro",
            apellidos="Usuario",
            email="otro@example.com",
            rol=Usuario.Rol.DIRECTOR_CARRERA,
            carrera=self.otra_carrera,
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
        self.otro_dimension = Dimension.objects.create(
            version=self.version,
            codigo="2",
            nombre="Recursos",
            orden=2,
        )
        self.indicador = Indicador.objects.create(
            dimension=self.dimension,
            codigo="1.1",
            texto="Indicador de prueba",
        )
        self.criterio = Criterio.objects.create(
            indicador=self.indicador,
            codigo="1.1.1",
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
        self.evidencia = Evidencia.objects.create(
            ciclo=self.ciclo,
            tipo_evidencia=self.tipo_evidencia,
            titulo="Memoria de autoevaluación",
            descripcion="Documento principal del ciclo",
            curso_academico=2025,
            periodo_desde=date(2025, 9, 1),
            periodo_hasta=date(2026, 6, 30),
            soporte=Evidencia.Soporte.DIGITAL,
        )
        AsignacionDimension.objects.create(
            ciclo=self.ciclo,
            usuario=self.usuario,
            dimension=self.dimension,
        )

    def test_crear_valoracion_guarda_relaciones_y_rechaza_usuario_sin_permiso(self):
        valoracion = crear_valoracion(
            self.ciclo,
            self.dimension,
            Valoracion.Tipo.FORTALEZA,
            "La propuesta tiene un enfoque sólido.",
            [self.criterio],
            [self.evidencia],
            usuario=self.usuario,
        )

        self.assertEqual(valoracion.criterios.count(), 1)
        self.assertEqual(valoracion.evidencias.count(), 1)

        with self.assertRaises(ValidationError):
            crear_valoracion(
                self.ciclo,
                self.dimension,
                Valoracion.Tipo.DEBILIDAD,
                "No debe permitirse",
                [self.criterio],
                [self.evidencia],
                usuario=self.otro_usuario,
            )

    def test_editar_valoracion_actualiza_texto_y_relaciones(self):
        valoracion = crear_valoracion(
            self.ciclo,
            self.dimension,
            Valoracion.Tipo.FORTALEZA,
            "Texto inicial",
            [self.criterio],
            [self.evidencia],
            usuario=self.usuario,
        )

        valoracion_actualizada = editar_valoracion(
            valoracion,
            texto="Texto actualizado",
            usuario=self.usuario,
        )

        self.assertEqual(valoracion_actualizada.texto, "Texto actualizado")
        self.assertEqual(valoracion_actualizada.criterios.count(), 1)

    def test_formatear_porcentaje_usa_coma_decimales_y_rechaza_cero(self):
        self.assertEqual(formatear_porcentaje(19, 22), "86,4 % (19/22)")

        with self.assertRaises(ValidationError):
            formatear_porcentaje(19, 0)

    def test_eliminar_valoracion_rechaza_si_hay_acciones_asociadas(self):
        valoracion = crear_valoracion(
            self.ciclo,
            self.dimension,
            Valoracion.Tipo.DEBILIDAD,
            "Debilidad con acciones asociadas",
            [self.criterio],
            [self.evidencia],
            usuario=self.usuario,
        )

        with patch("valoracion.servicios._depende_de_acciones_mejora", return_value=True):
            with self.assertRaises(ValidationError):
                eliminar_valoracion(valoracion, usuario=self.usuario)

    def test_registrar_creacion_y_edicion(self):
        valoracion = crear_valoracion(
            self.ciclo,
            self.dimension,
            Valoracion.Tipo.FORTALEZA,
            "Texto para registrar",
            [self.criterio],
            [self.evidencia],
            usuario=self.usuario,
        )

        editar_valoracion(
            valoracion,
            texto="Texto actualizado para registrar",
            usuario=self.usuario,
        )

        self.assertTrue(
            RegistroAuditoria.objects.filter(accion__in=["crear_valoracion", "editar_valoracion"]).exists()
        )


class ValoracionApiTests(TestCase):
    def setUp(self):
        self.facultad = Facultad.objects.create(nombre="Ingeniería")
        self.carrera = Carrera.objects.create(
            facultad=self.facultad,
            nombre="Ingeniería Informática",
            activa=True,
        )
        self.director = get_user_model().objects.create_user(
            "director-valoracion",
            "clave-segura-123",
            nombre="Directora",
            apellidos="Prueba",
            email="director@example.com",
            rol=Usuario.Rol.DIRECTOR_CARRERA,
            carrera=self.carrera,
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
            codigo="1.1",
            texto="Indicador de prueba",
        )
        self.criterio = Criterio.objects.create(
            indicador=self.indicador,
            codigo="1.1.1",
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
        self.evidencia = Evidencia.objects.create(
            ciclo=self.ciclo,
            tipo_evidencia=self.tipo_evidencia,
            titulo="Memoria de autoevaluación",
            descripcion="Documento principal del ciclo",
            curso_academico=2025,
            periodo_desde=date(2025, 9, 1),
            periodo_hasta=date(2026, 6, 30),
            soporte=Evidencia.Soporte.DIGITAL,
        )

    def test_post_crea_valoracion_en_ciclo(self):
        self.client.force_login(self.director)
        response = self.client.post(
            f"/api/ciclos/{self.ciclo.pk}/valoraciones/",
            {
                "dimension": self.dimension.pk,
                "tipo": "fortaleza",
                "texto": "Evaluación en API",
                "criterios": [self.criterio.pk],
                "evidencias": [self.evidencia.pk],
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["tipo"], "fortaleza")
        self.assertEqual(response.json()["dimension"], self.dimension.pk)

    def test_patch_y_delete_requieren_permiso_y_procesan_valoracion(self):
        valoracion = crear_valoracion(
            self.ciclo,
            self.dimension,
            Valoracion.Tipo.DEBILIDAD,
            "Texto inicial",
            [self.criterio],
            [self.evidencia],
            usuario=self.director,
        )
        self.client.force_login(self.director)

        response = self.client.patch(
            f"/api/valoraciones/{valoracion.pk}/",
            {"texto": "Texto actualizado"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["texto"], "Texto actualizado")

        delete_response = self.client.delete(f"/api/valoraciones/{valoracion.pk}/")
        self.assertEqual(delete_response.status_code, 204)

    def test_catalogo_por_ciclo_devuelve_dimensiones_y_criterios(self):
        self.client.force_login(self.director)
        response = self.client.get(f"/api/ciclos/{self.ciclo.pk}/valoraciones/catalogo/")

        self.assertEqual(response.status_code, 200)
        cuerpo = response.json()
        self.assertEqual(cuerpo["version"]["id"], self.version.pk)
        self.assertEqual(cuerpo["dimensiones"][0]["id"], self.dimension.pk)
        self.assertEqual(
            cuerpo["dimensiones"][0]["indicadores"][0]["criterios"][0]["id"],
            self.criterio.pk,
        )
