from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from ciclos.modelos import Carrera, Ciclo, Facultad
from estructura.models import (
    Criterio,
    CriterioModelo,
    Dimension,
    Indicador,
    ModeloCampo,
    ModeloDefinicion,
    TipoEvidencia,
    VersionNormativa,
)
from evidencias.modelos import Evidencia

from .models import ValorCriterio, ValorModelo, VinculoDato
from .servicios import (
    datos_de_evidencia,
    datos_sin_respaldo,
    desvincular,
    guardar_valor_criterio,
    guardar_valores_modelo,
    rellenar_acreditacion_anterior,
    vincular,
)


class CuantitativosModelosTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            "usuario-cuantitativos",
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
            codigo="1.1",
            texto="Indicador de prueba",
        )
        self.criterio = Criterio.objects.create(
            indicador=self.indicador,
            codigo="1.1.1",
            codigo_guia="C-1",
            solo_en_guia=False,
            texto="Criterio de prueba",
            tipo_dato=Criterio.TipoDato.CUANTITATIVO,
            valoracion_por_categoria=False,
        )
        self.modelo = ModeloDefinicion.objects.create(
            version=self.version,
            numero=1,
            nombre="Modelo de prueba",
        )
        self.campo = ModeloCampo.objects.create(
            modelo=self.modelo,
            fila=1,
            columna=1,
            tipo_valor=ModeloCampo.TipoValor.PORCENTAJE,
            orden=1,
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
            titulo="Documentación de evidencia",
            descripcion="Documento principal",
            curso_academico="2025-2026",
            periodo_desde=date(2025, 9, 1),
            periodo_hasta=date(2026, 6, 30),
            soporte=Evidencia.Soporte.DIGITAL,
        )

    def test_valor_modelo_rechaza_valores_negativos(self):
        valor = ValorModelo(
            ciclo=self.ciclo,
            campo=self.campo,
            curso=2025,
            valor=-1,
            numerador=2,
            denominador=3,
        )

        with self.assertRaises(ValidationError):
            valor.full_clean()

    def test_valor_modelo_rechaza_porcentaje_fuera_de_rango(self):
        valor = ValorModelo(
            ciclo=self.ciclo,
            campo=self.campo,
            curso=2025,
            valor=110,
            numerador=11,
            denominador=10,
        )

        with self.assertRaises(ValidationError):
            valor.full_clean()

    def test_valor_criterio_rechaza_criterio_que_tiene_modelo_o_es_cualitativo(self):
        CriterioModelo.objects.create(criterio=self.criterio, modelo=self.modelo)

        with self.assertRaises(ValidationError):
            ValorCriterio(
                ciclo=self.ciclo,
                criterio=self.criterio,
                valor=50,
                numerador=5,
                denominador=10,
                unidad="%",
            ).full_clean()

        criterio_cualitativo = Criterio.objects.create(
            indicador=self.indicador,
            codigo="1.1.2",
            codigo_guia="C-2",
            solo_en_guia=False,
            texto="Criterio cualitativo",
            tipo_dato=Criterio.TipoDato.CUALITATIVO,
            valoracion_por_categoria=False,
        )

        with self.assertRaises(ValidationError):
            ValorCriterio(
                ciclo=self.ciclo,
                criterio=criterio_cualitativo,
                valor=1,
                numerador=1,
                denominador=1,
                unidad="puntos",
            ).full_clean()

    def test_vinculo_dato_rechaza_dos_datos_a_la_vez(self):
        valor_modelo = ValorModelo.objects.create(
            ciclo=self.ciclo,
            campo=self.campo,
            curso=2025,
            valor=75,
            numerador=3,
            denominador=4,
        )
        valor_criterio = ValorCriterio.objects.create(
            ciclo=self.ciclo,
            criterio=self.criterio,
            valor=25,
            numerador=1,
            denominador=4,
            unidad="%",
        )

        with self.assertRaises(ValidationError):
            VinculoDato(
                evidencia=self.evidencia,
                valor_modelo=valor_modelo,
                valor_criterio=valor_criterio,
            ).full_clean()

    def test_vinculo_dato_requiere_mismo_ciclo_entre_dato_y_evidencia(self):
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
        valor_modelo = ValorModelo.objects.create(
            ciclo=otro_ciclo,
            campo=self.campo,
            curso=2025,
            valor=75,
            numerador=3,
            denominador=4,
        )

        with self.assertRaises(ValidationError):
            VinculoDato(
                evidencia=self.evidencia,
                valor_modelo=valor_modelo,
            ).full_clean()

    def test_valores_modelo_y_criterio_tienen_unicidad_por_ciclo_y_relacion(self):
        ValorModelo.objects.create(
            ciclo=self.ciclo,
            campo=self.campo,
            curso=2025,
            valor=80,
            numerador=4,
            denominador=5,
        )
        ValorCriterio.objects.create(
            ciclo=self.ciclo,
            criterio=self.criterio,
            valor=20,
            numerador=1,
            denominador=5,
            unidad="%",
        )

        duplicado_modelo = ValorModelo(
            ciclo=self.ciclo,
            campo=self.campo,
            curso=2025,
            valor=50,
        )
        duplicado_criterio = ValorCriterio(
            ciclo=self.ciclo,
            criterio=self.criterio,
            valor=10,
            numerador=1,
            denominador=10,
            unidad="%",
        )

        with self.assertRaises(ValidationError):
            duplicado_modelo.full_clean()

        with self.assertRaises(ValidationError):
            duplicado_criterio.full_clean()


class CuantitativosServiciosTests(TestCase):
    def setUp(self):
        self.facultad = Facultad.objects.create(nombre="Ingeniería")
        self.carrera = Carrera.objects.create(
            facultad=self.facultad,
            nombre="Ingeniería Informática",
            activa=True,
        )
        self.usuario = get_user_model().objects.create_user(
            "director-cuantitativos",
            "clave-segura-123",
            nombre="Director",
            apellidos="Carrera",
            email="director@example.com",
            rol=get_user_model().Rol.DIRECTOR_CARRERA,
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
            tipo_dato=Criterio.TipoDato.CUANTITATIVO,
            valoracion_por_categoria=False,
        )
        self.modelo = ModeloDefinicion.objects.create(
            version=self.version,
            numero=1,
            nombre="Modelo de prueba",
        )
        self.campo_porcentaje = ModeloCampo.objects.create(
            modelo=self.modelo,
            fila=1,
            columna=1,
            tipo_valor=ModeloCampo.TipoValor.PORCENTAJE,
            orden=1,
        )
        self.campo_entero = ModeloCampo.objects.create(
            modelo=self.modelo,
            fila=1,
            columna=2,
            tipo_valor=ModeloCampo.TipoValor.ENTERO,
            orden=2,
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
            titulo="Documentación de evidencia",
            descripcion="Documento principal",
            curso_academico="2025-2026",
            periodo_desde=date(2025, 9, 1),
            periodo_hasta=date(2026, 6, 30),
            soporte=Evidencia.Soporte.DIGITAL,
        )

    def test_guardar_valores_modelo_valida_porcentaje_y_guarda_resultados(self):
        registros = guardar_valores_modelo(
            self.ciclo,
            self.modelo,
            2025,
            {
                self.campo_porcentaje.pk: {"valor": 75, "numerador": 3, "denominador": 4},
                self.campo_entero.pk: {"valor": 12},
            },
            self.usuario,
        )

        self.assertEqual(len(registros), 2)
        self.assertEqual(ValorModelo.objects.filter(ciclo=self.ciclo, curso=2025).count(), 2)
        porcentaje = ValorModelo.objects.get(ciclo=self.ciclo, campo=self.campo_porcentaje, curso=2025)
        self.assertEqual(porcentaje.valor, Decimal("75"))
        self.assertEqual(porcentaje.numerador, Decimal("3"))
        self.assertEqual(porcentaje.denominador, Decimal("4"))

    def test_guardar_valor_criterio_rechaza_criterio_con_modelo_o_cualitativo(self):
        CriterioModelo.objects.create(criterio=self.criterio, modelo=self.modelo)
        with self.assertRaises(ValidationError):
            guardar_valor_criterio(
                self.ciclo,
                self.criterio,
                valor=50,
                numerador=1,
                denominador=2,
                usuario=self.usuario,
            )

        criterio_cualitativo = Criterio.objects.create(
            indicador=self.indicador,
            codigo="1.1.2",
            codigo_guia="C-2",
            solo_en_guia=False,
            texto="Criterio cualitativo",
            tipo_dato=Criterio.TipoDato.CUALITATIVO,
            valoracion_por_categoria=False,
        )

        with self.assertRaises(ValidationError):
            guardar_valor_criterio(
                self.ciclo,
                criterio_cualitativo,
                valor=1,
                numerador=1,
                denominador=1,
                usuario=self.usuario,
            )

    def test_rellenar_acreditacion_anterior_copia_valores_del_ciclo_previo(self):
        ciclo_anterior = Ciclo.objects.create(
            carrera=self.carrera,
            version_normativa=self.version,
            tipo="ordinario",
            anio_base=2025,
            curso_inicial=2020,
            curso_final=2024,
            estado=Ciclo.Estado.CERRADO,
            fecha_apertura=date(2025, 1, 1),
            fecha_cierre=date(2025, 12, 31),
        )
        valor_anterior = ValorModelo.objects.create(
            ciclo=ciclo_anterior,
            campo=self.campo_porcentaje,
            curso=2024,
            valor=80,
            numerador=4,
            denominador=5,
        )
        nuevo = ValorModelo.objects.create(
            ciclo=self.ciclo,
            campo=self.campo_porcentaje,
            curso=2024,
            valor=None,
            numerador=None,
            denominador=None,
        )

        self.ciclo.ciclo_anterior = ciclo_anterior
        self.ciclo.save(update_fields=["ciclo_anterior"])

        actualizados = rellenar_acreditacion_anterior(self.ciclo)
        nuevo.refresh_from_db()

        self.assertIn(nuevo, actualizados)
        self.assertEqual(nuevo.valor, valor_anterior.valor)

    def test_vinculacion_y_datos_sin_respaldo_recorren_ambos_sentidos(self):
        valor_modelo = ValorModelo.objects.create(
            ciclo=self.ciclo,
            campo=self.campo_porcentaje,
            curso=2025,
            valor=40,
            numerador=2,
            denominador=5,
        )

        self.assertIn(valor_modelo, datos_sin_respaldo(self.ciclo))
        self.assertEqual(datos_de_evidencia(self.evidencia), [])

        enlaces = vincular(valor_modelo, [self.evidencia], usuario=self.usuario)
        self.assertEqual(len(enlaces), 1)
        self.assertNotIn(valor_modelo, datos_sin_respaldo(self.ciclo))
        self.assertEqual(datos_de_evidencia(self.evidencia)[0], valor_modelo)

        desvincular(valor_modelo, [self.evidencia], usuario=self.usuario)
        self.assertIn(valor_modelo, datos_sin_respaldo(self.ciclo))
        self.assertEqual(datos_de_evidencia(self.evidencia), [])


class CuantitativosApiTests(TestCase):
    def setUp(self):
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
        self.usuario = get_user_model().objects.create_user(
            "director-cuantitativos-api",
            "clave-segura-123",
            nombre="Director",
            apellidos="Carrera",
            email="director-api@example.com",
            rol=get_user_model().Rol.DIRECTOR_CARRERA,
            carrera=self.carrera,
        )
        self.otro_usuario = get_user_model().objects.create_user(
            "otro-director-api",
            "clave-segura-123",
            nombre="Otro",
            apellidos="Director",
            email="otro-api@example.com",
            rol=get_user_model().Rol.DIRECTOR_CARRERA,
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
            tipo_dato=Criterio.TipoDato.CUANTITATIVO,
            valoracion_por_categoria=False,
        )
        self.modelo = ModeloDefinicion.objects.create(
            version=self.version,
            numero=1,
            nombre="Modelo de prueba",
        )
        self.campo_porcentaje = ModeloCampo.objects.create(
            modelo=self.modelo,
            fila=1,
            columna=1,
            tipo_valor=ModeloCampo.TipoValor.PORCENTAJE,
            orden=1,
        )
        self.campo_entero = ModeloCampo.objects.create(
            modelo=self.modelo,
            fila=1,
            columna=2,
            tipo_valor=ModeloCampo.TipoValor.ENTERO,
            orden=2,
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
            titulo="Documentación de evidencia",
            descripcion="Documento principal",
            curso_academico="2025-2026",
            periodo_desde=date(2025, 9, 1),
            periodo_hasta=date(2026, 6, 30),
            soporte=Evidencia.Soporte.DIGITAL,
        )

    def test_api_valores_de_modelo_y_criterio_funcionan_y_respetan_permisos(self):
        self.client.force_login(self.usuario)

        put_modelo = self.client.put(
            f"/api/ciclos/{self.ciclo.pk}/modelos/{self.modelo.numero}/valores/?curso=2025",
            data={
                "celdas": [
                    {"campo": self.campo_porcentaje.pk, "valor": 75, "numerador": 3, "denominador": 4},
                    {"campo": self.campo_entero.pk, "valor": 12},
                ]
            },
            content_type="application/json",
        )
        self.assertEqual(put_modelo.status_code, 200, put_modelo.content)
        self.assertEqual(ValorModelo.objects.filter(ciclo=self.ciclo, curso=2025).count(), 2)

        get_modelo = self.client.get(f"/api/ciclos/{self.ciclo.pk}/modelos/{self.modelo.numero}/valores/?curso=2025")
        self.assertEqual(get_modelo.status_code, 200)
        self.assertGreaterEqual(len(get_modelo.json()["celdas"]), 2)

        put_criterio = self.client.put(
            f"/api/ciclos/{self.ciclo.pk}/criterios/{self.criterio.codigo}/valor/",
            data={"valor": 50, "numerador": 1, "denominador": 2, "unidad": "%"},
            content_type="application/json",
        )
        self.assertEqual(put_criterio.status_code, 200, put_criterio.content)

        get_criterio = self.client.get(f"/api/ciclos/{self.ciclo.pk}/criterios/{self.criterio.codigo}/valor/")
        self.assertEqual(get_criterio.status_code, 200)
        self.assertEqual(get_criterio.json()["valor"]["valor"], 50)

        self.client.force_login(self.otro_usuario)
        denied = self.client.get(f"/api/ciclos/{self.ciclo.pk}/modelos/{self.modelo.numero}/valores/?curso=2025")
        self.assertEqual(denied.status_code, 403)

    def test_api_vinculos_y_datos_sin_respaldo_comparten_informacion(self):
        valor_modelo = ValorModelo.objects.create(
            ciclo=self.ciclo,
            campo=self.campo_porcentaje,
            curso=2025,
            valor=40,
            numerador=2,
            denominador=5,
        )

        self.client.force_login(self.usuario)
        response = self.client.post(
            "/api/vinculos/",
            data={"dato": {"tipo": "modelo", "id": valor_modelo.pk}, "evidencia": self.evidencia.pk},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201, response.content)

        evidencia_response = self.client.get(f"/api/evidencias/{self.evidencia.pk}/datos/")
        self.assertEqual(evidencia_response.status_code, 200)
        self.assertEqual(len(evidencia_response.json()["datos"]), 1)

        datos_response = self.client.get(f"/api/datos/modelo/{valor_modelo.pk}/evidencias/")
        self.assertEqual(datos_response.status_code, 200)
        self.assertEqual(len(datos_response.json()["evidencias"]), 1)

        sin_respaldo = self.client.get(f"/api/ciclos/{self.ciclo.pk}/datos/sin-respaldo/")
        self.assertEqual(sin_respaldo.status_code, 200)
        self.assertNotIn(valor_modelo.pk, [item["id"] for item in sin_respaldo.json()["datos"]])

        self.client.force_login(self.otro_usuario)
        denied = self.client.get(f"/api/ciclos/{self.ciclo.pk}/datos/sin-respaldo/")
        self.assertEqual(denied.status_code, 403)
