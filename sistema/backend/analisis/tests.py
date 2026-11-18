from django.test import SimpleTestCase

from .estructuras import (
    ComparacionPayload,
    CompletitudPayload,
    CriterioEstado,
    DimensionEstado,
    EstadoCicloPayload,
    IndicadorEstado,
)


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
