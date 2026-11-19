from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from rest_framework.test import APIClient

from auditoria.modelos import RegistroAuditoria
from ciclos.modelos import Carrera, Ciclo, Facultad
from mejora.modelos import AccionMejora, PlanMejora
from cuantitativos.models import ValorModelo
from estructura.models import (
    Criterio,
    CriterioModelo,
    Dimension,
    Indicador,
    ModeloCampo,
    ModeloDefinicion,
    VersionNormativa,
)
from valoracion.models import Valoracion, ValoracionCriterio

from .estructuras import (
    ComparacionPayload,
    CompletitudPayload,
    CriterioEstado,
    DimensionEstado,
    EstadoCicloPayload,
    IndicadorEstado,
)
from .servicios import comparar, completitud, estado_ciclo


class PayloadsAnalisisTests(SimpleTestCase):
    def test_estado_payload_completo_se_serializa_sin_categoria(self):
        criterio = CriterioEstado(
            id=1,
            codigo="1.1.1",
            nombre="Criterio de prueba",
            evidencias_clasificadas=2,
            datos_cuantitativos=True,
            dato_con_respaldo=True,
            tiene_valoracion=True,
            tiene_accion=True,
        )
        indicador = IndicadorEstado(
            id=10,
            codigo="1.1",
            nombre="Indicador de prueba",
            criterios=(criterio,),
        )
        dimension = DimensionEstado(
            id=100,
            codigo="1",
            nombre="Dimensión de prueba",
            indicadores=(indicador,),
        )

        payload = EstadoCicloPayload(ciclo_id=7, dimensiones=(dimension,)).to_dict()

        self.assertEqual(payload["ciclo_id"], 7)
        self.assertEqual(payload["dimensiones"][0]["indicadores"][0]["criterios"][0]["id"], 1)
        self.assertNotIn("categoria", payload)
        self.assertNotIn("categoria_acreditacion", payload)


class ServiciosAnalisisTests(TestCase):
    def setUp(self):
        self.facultad = Facultad.objects.create(nombre="Ingeniería")
        self.carrera = Carrera.objects.create(
            facultad=self.facultad,
            nombre="Sistemas",
        )
        self.otra_carrera = Carrera.objects.create(
            facultad=self.facultad,
            nombre="Civil",
        )
        self.version = VersionNormativa.objects.create(
            nombre="SEA-CU 2025",
            fecha_aprobacion=date(2025, 1, 1),
            fuentes="Fuentes",
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
            texto="Indicador",
        )
        self.criterio = Criterio.objects.create(
            indicador=self.indicador,
            codigo="1.1.1",
            codigo_guia="C-1",
            solo_en_guia=False,
            texto="Criterio",
            tipo_dato=Criterio.TipoDato.CUANTITATIVO,
            valoracion_por_categoria=False,
        )
        self.modelo = ModeloDefinicion.objects.create(
            version=self.version,
            numero=1,
            nombre="Modelo",
        )
        self.campo = ModeloCampo.objects.create(
            modelo=self.modelo,
            fila=1,
            columna=1,
            tipo_valor=ModeloCampo.TipoValor.PORCENTAJE,
            orden=1,
        )
        CriterioModelo.objects.create(
            criterio=self.criterio,
            modelo=self.modelo,
        )
        self.ciclo_a = Ciclo.objects.create(
            carrera=self.carrera,
            version_normativa=self.version,
            tipo="ordinario",
            anio_base=2026,
            curso_inicial=2021,
            curso_final=2025,
            estado=Ciclo.Estado.CERRADO,
            fecha_apertura=date(2021, 9, 1),
            fecha_cierre=date(2026, 6, 30),
        )
        self.ciclo_b = Ciclo.objects.create(
            carrera=self.carrera,
            version_normativa=self.version,
            tipo="ordinario",
            anio_base=2031,
            curso_inicial=2031,
            curso_final=2035,
            estado=Ciclo.Estado.ABIERTO,
            fecha_apertura=date(2031, 9, 1),
        )
        self.director = get_user_model().objects.create_user(
            "director-analisis",
            "clave-segura-123",
            nombre="Director",
            apellidos="Análisis",
            email="director-analisis@example.com",
            rol=get_user_model().Rol.DIRECTOR_CARRERA,
            carrera=self.carrera,
        )

    def test_estado_ciclo_cerrado_recorre_arbol_sin_calcular_categoria(self):
        payload = estado_ciclo(self.ciclo_a).to_dict()

        self.assertEqual(payload["ciclo_id"], self.ciclo_a.pk)
        self.assertEqual(payload["dimensiones"][0]["indicadores"][0]["criterios"][0]["id"], self.criterio.pk)
        self.assertNotIn("categoria", payload)

    def test_completitud_devuelve_los_seis_tipos_de_aviso_y_modelo_incompleto(self):
        payload = completitud(self.ciclo_a).to_dict()

        self.assertIn(self.criterio.pk, payload["criterios_sin_evidencia"])
        self.assertIn(self.criterio.pk, payload["criterios_cuantitativos_sin_dato"])
        self.assertIn(self.dimension.pk, payload["dimensiones_sin_valoracion"])
        self.assertEqual(len(payload["modelos_incompletos"]), 5)
        self.assertEqual(
            set(payload),
            {
                "ciclo_id",
                "criterios_sin_evidencia",
                "criterios_cuantitativos_sin_dato",
                "datos_sin_respaldo",
                "modelos_incompletos",
                "dimensiones_sin_valoracion",
                "debilidades_sin_accion",
            },
        )

    def test_completitud_excluye_dimension_con_valoracion_por_criterio(self):
        otra_dimension = Dimension.objects.create(
            version=self.version,
            codigo="2",
            nombre="Impacto",
            orden=2,
        )
        otro_indicador = Indicador.objects.create(
            dimension=otra_dimension,
            codigo="2.1",
            texto="Indicador 2",
        )
        Criterio.objects.create(
            indicador=otro_indicador,
            codigo="2.1.1",
            codigo_guia="C-2",
            solo_en_guia=False,
            texto="Otro criterio",
            tipo_dato=Criterio.TipoDato.CUALITATIVO,
            valoracion_por_categoria=False,
        )
        valoracion = Valoracion.objects.create(
            ciclo=self.ciclo_b,
            dimension=self.dimension,
            tipo=Valoracion.Tipo.FORTALEZA,
            texto="Fortaleza validada",
            redactada_por=self.director,
        )
        ValoracionCriterio.objects.create(
            valoracion=valoracion,
            criterio=self.criterio,
        )

        payload = completitud(self.ciclo_b).to_dict()

        self.assertNotIn(self.dimension.pk, payload["dimensiones_sin_valoracion"])
        self.assertIn(otra_dimension.pk, payload["dimensiones_sin_valoracion"])

    def test_completitud_detecta_debilidades_sin_accion(self):
        debilidad_sin_accion = Valoracion.objects.create(
            ciclo=self.ciclo_b,
            dimension=self.dimension,
            tipo=Valoracion.Tipo.DEBILIDAD,
            texto="Debilidad sin plan",
            redactada_por=self.director,
        )
        ValoracionCriterio.objects.create(
            valoracion=debilidad_sin_accion,
            criterio=self.criterio,
        )
        debilidad_con_accion = Valoracion.objects.create(
            ciclo=self.ciclo_b,
            dimension=self.dimension,
            tipo=Valoracion.Tipo.DEBILIDAD,
            texto="Debilidad con acción",
            redactada_por=self.director,
        )
        ValoracionCriterio.objects.create(
            valoracion=debilidad_con_accion,
            criterio=self.criterio,
        )
        plan = PlanMejora.objects.create(ciclo=self.ciclo_b)
        AccionMejora.objects.create(
            plan=plan,
            debilidad=debilidad_con_accion,
            descripcion="Atender debilidad",
            responsable=self.director,
            fecha_limite=date(2032, 6, 1),
        )

        payload = completitud(self.ciclo_b).to_dict()

        self.assertIn(debilidad_sin_accion.pk, payload["debilidades_sin_accion"])
        self.assertNotIn(debilidad_con_accion.pk, payload["debilidades_sin_accion"])

    def test_comparar_usa_posicion_relativa_y_registra_comparacion(self):
        ValorModelo.objects.create(
            ciclo=self.ciclo_a,
            campo=self.campo,
            curso=2021,
            valor=Decimal("50"),
        )
        ValorModelo.objects.create(
            ciclo=self.ciclo_b,
            campo=self.campo,
            curso=2031,
            valor=Decimal("75"),
        )

        payload = comparar(
            self.ciclo_a,
            self.ciclo_b,
            usuario=self.director,
        ).to_dict()

        self.assertEqual(len(payload["diferencias_modelos"]), 1)
        diferencia = payload["diferencias_modelos"][0]
        self.assertEqual(diferencia["posicion_relativa"], 0)
        self.assertEqual(diferencia["curso_a"], 2021)
        self.assertEqual(diferencia["curso_b"], 2031)
        self.assertTrue(
            RegistroAuditoria.objects.filter(
                accion="comparar_ciclos",
                usuario=self.director,
            ).exists()
        )

    def test_comparar_rechaza_sesion_ausente_y_carreras_distintas(self):
        with self.assertRaises(ValidationError):
            comparar(self.ciclo_a, self.ciclo_b, usuario=None)

        ciclo_otra = Ciclo.objects.create(
            carrera=self.otra_carrera,
            version_normativa=self.version,
            tipo="ordinario",
            anio_base=2026,
            curso_inicial=2021,
            curso_final=2025,
            estado=Ciclo.Estado.ABIERTO,
            fecha_apertura=date(2026, 1, 1),
        )
        with self.assertRaises(ValidationError):
            comparar(self.ciclo_a, ciclo_otra)

    def test_estado_payload_vacio_tiene_lista_de_dimensiones(self):
        payload = EstadoCicloPayload(ciclo_id=7).to_dict()

        self.assertEqual(payload, {"ciclo_id": 7, "dimensiones": []})

    def test_completitud_payload_incluye_las_seis_claves_sin_categoria(self):
        payload = CompletitudPayload(
            ciclo_id=7,
            criterios_sin_evidencia=(1,),
        ).to_dict()

        self.assertEqual(
            set(payload),
            {
                "ciclo_id",
                "criterios_sin_evidencia",
                "criterios_cuantitativos_sin_dato",
                "datos_sin_respaldo",
                "modelos_incompletos",
                "dimensiones_sin_valoracion",
                "debilidades_sin_accion",
            },
        )
        self.assertEqual(payload["criterios_sin_evidencia"], [1])
        self.assertNotIn("categoria", payload)
        self.assertNotIn("categoria_acreditacion", payload)

    def test_completitud_payload_vacio_tiene_todos_los_tipos_de_aviso(self):
        payload = CompletitudPayload(ciclo_id=7).to_dict()

        for clave in (
            "criterios_sin_evidencia",
            "criterios_cuantitativos_sin_dato",
            "datos_sin_respaldo",
            "modelos_incompletos",
            "dimensiones_sin_valoracion",
            "debilidades_sin_accion",
        ):
            self.assertEqual(payload[clave], [])

    def test_comparacion_payload_vacio_se_serializa_con_los_tres_bloques(self):
        payload = ComparacionPayload(ciclo_a_id=7, ciclo_b_id=8).to_dict()

        self.assertEqual(
            payload,
            {
                "ciclo_a_id": 7,
                "ciclo_b_id": 8,
                "diferencias_modelos": [],
                "diferencias_criterios": [],
                "diferencias_acciones": [],
            },
        )
        self.assertNotIn("categoria", payload)
        self.assertNotIn("categoria_acreditacion", payload)


class ApiAnalisisTests(TestCase):
    def setUp(self):
        self.client_api = APIClient()
        self.facultad = Facultad.objects.create(nombre="Ingeniería")
        self.carrera = Carrera.objects.create(facultad=self.facultad, nombre="Sistemas")
        self.otra_carrera = Carrera.objects.create(facultad=self.facultad, nombre="Civil")
        self.version = VersionNormativa.objects.create(
            nombre="SEA-CU API",
            fecha_aprobacion=date(2026, 1, 1),
            fuentes="Fuentes",
            activa=True,
        )
        self.ciclo_a = Ciclo.objects.create(
            carrera=self.carrera,
            version_normativa=self.version,
            tipo="ordinario",
            anio_base=2026,
            curso_inicial=2021,
            curso_final=2025,
            estado=Ciclo.Estado.CERRADO,
            fecha_apertura=date(2021, 9, 1),
            fecha_cierre=date(2026, 6, 30),
        )
        self.ciclo_b = Ciclo.objects.create(
            carrera=self.carrera,
            version_normativa=self.version,
            tipo="ordinario",
            anio_base=2031,
            curso_inicial=2031,
            curso_final=2035,
            estado=Ciclo.Estado.ABIERTO,
            fecha_apertura=date(2031, 9, 1),
        )
        self.ciclo_otra = Ciclo.objects.create(
            carrera=self.otra_carrera,
            version_normativa=self.version,
            tipo="ordinario",
            anio_base=2026,
            curso_inicial=2021,
            curso_final=2025,
            estado=Ciclo.Estado.CERRADO,
            fecha_apertura=date(2021, 9, 1),
            fecha_cierre=date(2026, 6, 30),
        )
        self.admin = get_user_model().objects.create_user(
            "admin-api-analisis",
            "clave-segura-123",
            nombre="Administrador",
            apellidos="Técnico",
            email="admin-api-analisis@example.com",
            rol=get_user_model().Rol.ADMINISTRADOR_TECNICO,
        )
        self.director = get_user_model().objects.create_user(
            "director-api-analisis",
            "clave-segura-123",
            nombre="Director",
            apellidos="Carrera",
            email="director-api-analisis@example.com",
            rol=get_user_model().Rol.DIRECTOR_CARRERA,
            carrera=self.carrera,
        )

    def test_estado_y_completitud_aceptan_ciclo_cerrado_autenticado(self):
        self.client_api.force_authenticate(user=self.admin)

        estado = self.client_api.get(f"/api/ciclos/{self.ciclo_a.pk}/estado/")
        completitud = self.client_api.get(
            f"/api/ciclos/{self.ciclo_a.pk}/completitud/"
        )

        self.assertEqual(estado.status_code, 200)
        self.assertEqual(completitud.status_code, 200)
        self.assertIn("dimensiones", estado.json())
        self.assertIn("criterios_sin_evidencia", completitud.json())

    def test_sesion_django_puede_consultar_estado(self):
        self.client_api.force_login(self.admin)

        respuesta = self.client_api.get(
            f"/api/ciclos/{self.ciclo_a.pk}/estado/"
        )

        self.assertEqual(respuesta.status_code, 200)

    def test_apis_rechazan_sesion_ausente_con_formato_estandar(self):
        estado = self.client_api.get(f"/api/ciclos/{self.ciclo_a.pk}/estado/")
        comparacion = self.client_api.get(
            f"/api/comparaciones/?a={self.ciclo_a.pk}&b={self.ciclo_b.pk}"
        )

        self.assertEqual(estado.status_code, 403)
        self.assertEqual(comparacion.status_code, 403)
        for respuesta in (estado, comparacion):
            payload = respuesta.json()
            self.assertEqual(
                set(payload),
                {"codigo", "mensaje", "detalle"},
            )
            self.assertEqual(payload["codigo"], "autenticacion_requerida")

    def test_comparacion_valida_y_rechazos_basicos(self):
        self.client_api.force_authenticate(user=self.director)

        valida = self.client_api.get(
            f"/api/comparaciones/?a={self.ciclo_a.pk}&b={self.ciclo_b.pk}"
        )
        faltantes = self.client_api.get("/api/comparaciones/?a=")
        mismo = self.client_api.get(
            f"/api/comparaciones/?a={self.ciclo_a.pk}&b={self.ciclo_a.pk}"
        )
        carreras_distintas = self.client_api.get(
            f"/api/comparaciones/?a={self.ciclo_a.pk}&b={self.ciclo_otra.pk}"
        )
        inexistente = self.client_api.get(
            f"/api/comparaciones/?a=999999&b={self.ciclo_b.pk}"
        )

        self.assertEqual(valida.status_code, 200)
        self.assertEqual(faltantes.status_code, 400)
        self.assertEqual(faltantes.json()["codigo"], "parametros_invalidos")
        self.assertEqual(mismo.status_code, 400)
        self.assertEqual(mismo.json()["codigo"], "comparacion_invalida")
        self.assertEqual(carreras_distintas.status_code, 400)
        self.assertEqual(carreras_distintas.json()["codigo"], "carreras_distintas")
        self.assertEqual(inexistente.status_code, 404)
        self.assertEqual(inexistente.json()["codigo"], "ciclo_no_encontrado")

    def test_director_fuera_de_carrera_recibe_403_sin_registro_duplicado(self):
        otra_director = get_user_model().objects.create_user(
            "director-api-civil",
            "clave-segura-123",
            nombre="Director",
            apellidos="Civil",
            email="director-api-civil@example.com",
            rol=get_user_model().Rol.DIRECTOR_CARRERA,
            carrera=self.otra_carrera,
        )
        self.client_api.force_authenticate(user=otra_director)

        antes = RegistroAuditoria.objects.filter(
            accion="acceso.denegado",
            usuario=otra_director,
        ).count()
        respuesta = self.client_api.get(
            f"/api/comparaciones/?a={self.ciclo_a.pk}&b={self.ciclo_b.pk}"
        )

        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(respuesta.json()["codigo"], "permiso_denegado")
        self.assertEqual(
            RegistroAuditoria.objects.filter(
                accion="acceso.denegado",
                usuario=otra_director,
            ).count(),
            antes + 1,
        )
