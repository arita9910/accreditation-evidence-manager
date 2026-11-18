import importlib
import json
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import Resolver404, clear_url_caches, resolve

from .models import (
    Criterio,
    CriterioModelo,
    Dimension,
    EvidenciaSugerida,
    Indicador,
    ModeloCampo,
    ModeloDefinicion,
    RequisitoCategoria,
    TipoEvidencia,
    VersionNormativa,
)
from .servicios import ErrorCatalogo, _preparar_importacion, cargar_catalogo, leer_catalogo


def crear_catalogo_completo():
    dimensiones = []
    criterios_globales = 0
    for numero_dimension in range(1, 7):
        indicadores = []
        codigo_dimension = str(numero_dimension)
        for numero_indicador in range(1, 5):
            codigo_indicador = f"{codigo_dimension}.{numero_indicador}"
            cantidad_criterios = 3 if numero_indicador <= 3 else 2
            if numero_dimension == 6 and numero_indicador >= 3:
                cantidad_criterios = 2
            if numero_dimension == 6 and numero_indicador == 2:
                cantidad_criterios = 3
            criterios = []
            for numero_criterio in range(1, cantidad_criterios + 1):
                codigo = f"{codigo_indicador}.{numero_criterio}"
                if (
                    numero_dimension == 3
                    and numero_indicador == 2
                    and numero_criterio == 3
                ):
                    codigo = "3.2.4"
                modelos_manual = ""
                if criterios_globales == 0:
                    modelos_manual = "M7 (7.1)"
                elif criterios_globales == 1:
                    modelos_manual = "M1, M2"
                elif criterios_globales == 2:
                    modelos_manual = "M3, M4"
                elif criterios_globales < 20:
                    modelos_manual = f"M{((criterios_globales - 2) % 11) + 1}"
                criterios_globales += 1
                criterios.append(
                    {
                        "criterio": codigo,
                        "codigo_manual": None if codigo == "3.2.4" else codigo,
                        "criterio_texto": f"Texto del criterio {codigo}",
                        "codigo_guia": codigo,
                        "solo_en_guia": "sí" if codigo == "3.2.4" else "no",
                        "tipo_dato": "Cuantitativo" if numero_criterio % 2 else "Cualitativo",
                        "modelos_manual": modelos_manual,
                        "requisito_por_categoria": "sí",
                        "evidencias_guia": (
                            "Entrevista a docentes | Visita a una entidad | Acta de reunión"
                        ),
                        "requisito_calificada": f"Calificada {codigo}",
                        "requisito_certificada": "",
                        "requisito_excelencia": "",
                        "requisito_unico": "",
                        "nota_normativa": "",
                    }
                )
            indicadores.append(
                {
                    "codigo": codigo_indicador,
                    "texto": f"Texto completo del indicador {codigo_indicador}",
                    "criterios": criterios,
                }
            )
        dimensiones.append(
            {"nombre": f"{codigo_dimension} Dimensión {codigo_dimension}", "indicadores": indicadores}
        )

    modelos = []
    for numero in range(1, 12):
        modelos.append(
            {
                "codigo": f"M{numero}",
                "numero": numero,
                "nombre": {"valor": f"Modelo {numero}"},
                "numero_rm36": {"valor": None},
                "celdas": {
                    "items": [
                        {
                            "fila": 1,
                            "columna": 1,
                            "tipo_valor": "entero",
                            "orden": 1,
                        },
                        {
                            "fila": 1,
                            "columna": 2,
                            "tipo_valor": "porcentaje",
                            "orden": 2,
                        },
                    ]
                },
            }
        )
    return (
        {
            "catalogo": "SEA-CU 2025",
            "version": "v3",
            "fecha_aprobacion": "2024-04-29",
            "fuente": "Fuente de fixture",
            "resumen": {"dimensiones": 6, "indicadores": 24, "criterios": 65},
            "dimensiones": dimensiones,
        },
        {"modelos": modelos},
    )


@contextmanager
def catalogo_api_habilitado():
    from config import urls

    try:
        with override_settings(CATALOGO_API_DESARROLLO=True):
            importlib.reload(urls)
            clear_url_caches()
            yield
    finally:
        importlib.reload(urls)
        clear_url_caches()


class LectorCatalogoTests(TestCase):
    def escribir_catalogo(self, datos):
        directorio = TemporaryDirectory()
        self.addCleanup(directorio.cleanup)
        ruta = Path(directorio.name) / "catalogo.json"
        ruta.write_text(json.dumps(datos), encoding="utf-8")
        return ruta

    def test_lee_el_formato_real_y_rechaza_totales_incorrectos(self):
        datos = leer_catalogo()
        self.assertEqual(len(datos["dimensiones"]), 6)
        self.assertEqual(
            sum(len(dimension["indicadores"]) for dimension in datos["dimensiones"]),
            24,
        )
        self.assertEqual(
            sum(
                len(indicador["criterios"])
                for dimension in datos["dimensiones"]
                for indicador in dimension["indicadores"]
            ),
            65,
        )

        fixture, _ = crear_catalogo_completo()
        fixture["dimensiones"][-1]["indicadores"][-1]["criterios"].pop()
        with self.assertRaisesRegex(ErrorCatalogo, "totales"):
            leer_catalogo(self.escribir_catalogo(fixture))

    def test_rechaza_dimensiones_fuera_del_prefijo_numerico_observado(self):
        fixture, _ = crear_catalogo_completo()
        fixture["dimensiones"][0]["nombre"] = "Dimensión sin código"

        with self.assertRaisesRegex(ErrorCatalogo, "código numérico"):
            leer_catalogo(self.escribir_catalogo(fixture))

    def test_acepta_etiquetas_de_celda_en_json_de_modelos(self):
        fixture, datos_modelos = crear_catalogo_completo()
        datos_modelos["modelos"][0]["celdas"]["items"][0]["etiqueta_fila"] = "Total del claustro"
        datos_modelos["modelos"][0]["celdas"]["items"][0]["etiqueta_columna"] = "Acreditación anterior"

        plan = _preparar_importacion(fixture, datos_modelos)

        self.assertEqual(
            plan["modelos"][1]["campos"][0]["etiqueta_fila"],
            "Total del claustro",
        )
        self.assertEqual(
            plan["modelos"][1]["campos"][0]["etiqueta_columna"],
            "Acreditación anterior",
        )


class CargaCatalogoTests(TestCase):
    def setUp(self):
        self.directorio = TemporaryDirectory()
        self.addCleanup(self.directorio.cleanup)
        self.ruta_catalogo = Path(self.directorio.name) / "catalogo.json"
        self.ruta_modelos = Path(self.directorio.name) / "modelos.json"
        self.datos, self.datos_modelos = crear_catalogo_completo()
        self._escribir_fuentes()

    def _escribir_fuentes(self):
        self.ruta_catalogo.write_text(json.dumps(self.datos), encoding="utf-8")
        self.ruta_modelos.write_text(json.dumps(self.datos_modelos), encoding="utf-8")

    def cargar(self):
        return cargar_catalogo(self.ruta_catalogo, self.ruta_modelos)

    def test_carga_repetible_mapea_evidencias_requisitos_y_modelos(self):
        nombre_version = "SEA-CU 2025 v3"
        version_preexistente = VersionNormativa.objects.create(
            nombre=nombre_version,
            fecha_aprobacion="2023-01-01",
            fuentes="Versión anterior",
            activa=False,
        )

        primer_resultado = self.cargar()
        segundo_resultado = self.cargar()

        self.assertEqual(primer_resultado["dimensiones"], 6)
        self.assertEqual(primer_resultado["indicadores"], 24)
        self.assertEqual(primer_resultado["criterios"], 65)
        self.assertEqual(primer_resultado["modelos"], 11)
        self.assertEqual(primer_resultado["asociaciones"], 22)
        self.assertEqual(primer_resultado["campos_modelo"], 22)
        self.assertEqual(segundo_resultado["asociaciones"], 22)
        self.assertEqual(segundo_resultado["campos_modelo"], 22)
        self.assertEqual(VersionNormativa.objects.count(), 1)
        self.assertEqual(Dimension.objects.count(), 6)
        self.assertEqual(Indicador.objects.count(), 24)
        self.assertEqual(Criterio.objects.count(), 65)
        self.assertEqual(ModeloDefinicion.objects.count(), 11)
        self.assertEqual(ModeloCampo.objects.count(), 22)
        self.assertEqual(CriterioModelo.objects.count(), 22)
        self.assertEqual(
            CriterioModelo.objects.values("criterio_id").distinct().count(),
            20,
        )
        self.assertEqual(
            VersionNormativa.objects.get().pk,
            version_preexistente.pk,
        )

        criterio_m7 = Criterio.objects.get(codigo="1.1.1")
        relacion = CriterioModelo.objects.get(criterio=criterio_m7)
        self.assertEqual(relacion.modelo.numero, 7)
        self.assertEqual(criterio_m7.nota_normativa, "7.1")
        self.assertEqual(criterio_m7.evidencias_sugeridas.count(), 3)
        self.assertTrue(
            criterio_m7.evidencias_sugeridas.get(orden=1).es_verificacion_externa
        )
        self.assertTrue(
            criterio_m7.evidencias_sugeridas.get(orden=2).es_verificacion_externa
        )
        self.assertEqual(criterio_m7.requisitos_categoria.count(), 1)
        criterio_solo_guia = Criterio.objects.get(codigo="3.2.4")
        self.assertTrue(criterio_solo_guia.solo_en_guia)
        self.assertIsNone(criterio_solo_guia.codigo_manual)
        self.assertEqual(TipoEvidencia.objects.count(), 0)
        self.assertEqual(
            ModeloCampo.objects.values("modelo_id").distinct().count(),
            11,
        )

    def test_falla_dentro_de_transaccion_y_revierte_toda_la_carga(self):
        with patch(
            "estructura.servicios._crear_evidencias",
            side_effect=RuntimeError("fallo de fixture"),
        ):
            with self.assertRaisesRegex(RuntimeError, "fallo de fixture"):
                self.cargar()

        self.assertEqual(VersionNormativa.objects.count(), 0)
        self.assertEqual(Dimension.objects.count(), 0)
        self.assertEqual(Criterio.objects.count(), 0)

    def test_comando_informa_campos_obligatorios_sin_mutar_la_base(self):
        self.datos.pop("fecha_aprobacion")
        self.datos["dimensiones"][0]["indicadores"][0].pop("texto")
        self.datos_modelos["modelos"][0]["nombre"]["valor"] = None
        self._escribir_fuentes()

        with self.assertRaises(CommandError) as error:
            call_command(
                "cargar_catalogo",
                catalogo=str(self.ruta_catalogo),
                modelos=str(self.ruta_modelos),
            )

        self.assertIn("fecha_aprobacion", str(error.exception))
        self.assertIn("dimensiones[1].indicadores[1].texto", str(error.exception))
        self.assertIn("modelos[1].nombre.valor", str(error.exception))
        self.assertEqual(VersionNormativa.objects.count(), 0)
        self.assertEqual(TipoEvidencia.objects.count(), 0)
        self.assertEqual(ModeloCampo.objects.count(), 0)

    def test_entrada_con_campos_obligatorios_faltantes_no_crea_registros(self):
        self.datos["fecha_aprobacion"] = ""
        self._escribir_fuentes()

        with self.assertRaisesRegex(ValueError, "fecha_aprobacion"):
            self.cargar()

        self.assertEqual(VersionNormativa.objects.count(), 0)
        self.assertEqual(Dimension.objects.count(), 0)

    def test_rechaza_coordenadas_duplicadas_en_modelo_campo(self):
        self.datos_modelos["modelos"][0]["celdas"]["items"].append(
            {"fila": 1, "columna": 1, "tipo_valor": "entero", "orden": 3}
        )
        self._escribir_fuentes()

        with self.assertRaisesRegex(ErrorCatalogo, "repite la coordenada"):
            self.cargar()

    def test_coinciden_totales_de_asociaciones_y_campos_con_fuentes(self):
        resultado = self.cargar()
        total_campos = sum(
            len(modelo["celdas"]["items"])
            for modelo in self.datos_modelos["modelos"]
        )
        total_asociaciones = sum(
            len(
                [valor for valor in criterio.get("modelos_manual", "").split(",") if valor.strip()]
            )
            for dimension in self.datos["dimensiones"]
            for indicador in dimension["indicadores"]
            for criterio in indicador["criterios"]
        )

        self.assertEqual(resultado["campos_modelo"], total_campos)
        self.assertEqual(resultado["asociaciones"], total_asociaciones)
        self.assertEqual(ModeloCampo.objects.count(), total_campos)
        self.assertEqual(CriterioModelo.objects.count(), total_asociaciones)

    def test_carga_y_actualiza_etiquetas_de_modelo_campo(self):
        self.datos_modelos["modelos"][0]["celdas"]["items"][0]["etiqueta_fila"] = "Docentes"
        self.datos_modelos["modelos"][0]["celdas"]["items"][0]["etiqueta_columna"] = "Año base"
        self._escribir_fuentes()

        self.cargar()

        campo = ModeloCampo.objects.get(modelo__numero=1, fila=1, columna=1)
        self.assertEqual(campo.etiqueta_fila, "Docentes")
        self.assertEqual(campo.etiqueta_columna, "Año base")

        self.datos_modelos["modelos"][0]["celdas"]["items"][0]["etiqueta_fila"] = "Académicos"
        self.datos_modelos["modelos"][0]["celdas"]["items"][0]["etiqueta_columna"] = "Año actual"
        self._escribir_fuentes()

        self.cargar()

        campo.refresh_from_db()
        self.assertEqual(campo.etiqueta_fila, "Académicos")
        self.assertEqual(campo.etiqueta_columna, "Año actual")


class CatalogoAPITests(TestCase):
    def setUp(self):
        self.directorio = TemporaryDirectory()
        self.addCleanup(self.directorio.cleanup)
        self.ruta_catalogo = Path(self.directorio.name) / "catalogo.json"
        self.ruta_modelos = Path(self.directorio.name) / "modelos.json"
        datos, datos_modelos = crear_catalogo_completo()
        self.ruta_catalogo.write_text(json.dumps(datos), encoding="utf-8")
        self.ruta_modelos.write_text(json.dumps(datos_modelos), encoding="utf-8")
        cargar_catalogo(self.ruta_catalogo, self.ruta_modelos)

    def test_api_no_se_expone_por_defecto(self):
        with self.assertRaises(Resolver404):
            resolve("/api/catalogo/")

    def test_api_solo_lectura_expone_arbol_modelos_versiones_y_ficha(self):
        with catalogo_api_habilitado():
            arbol = self.client.get("/api/catalogo/")
            self.assertEqual(arbol.status_code, 200)
            datos = arbol.json()
            self.assertEqual(len(datos["dimensiones"]), 6)
            self.assertEqual(
                sum(len(dimension["indicadores"]) for dimension in datos["dimensiones"]),
                24,
            )
            self.assertEqual(
                sum(
                    len(indicador["criterios"])
                    for dimension in datos["dimensiones"]
                    for indicador in dimension["indicadores"]
                ),
                65,
            )

            ficha = self.client.get("/api/catalogo/criterios/1.1.1/")
            self.assertEqual(ficha.status_code, 200)
            self.assertEqual(ficha.json()["modelos"][0]["numero"], 7)
            self.assertEqual(ficha.json()["nota_normativa"], "7.1")
            self.assertEqual(
                self.client.get("/api/catalogo/modelos/").status_code,
                200,
            )
            self.assertEqual(
                self.client.get("/api/catalogo/versiones/").status_code,
                200,
            )

            inexistente = self.client.get("/api/catalogo/criterios/no-existe/")
            self.assertEqual(inexistente.status_code, 404)
            self.assertEqual(inexistente.json()["codigo"], "not_found")
            self.assertEqual(self.client.post("/api/catalogo/").status_code, 405)
            self.assertEqual(
                self.client.post("/api/catalogo/criterios/1.1.1/").status_code,
                405,
            )
