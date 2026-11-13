from decimal import Decimal

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from ciclos.modelos import Ciclo
from cuentas.permisos import PermisoSistema, puede
from estructura.models import Criterio, ModeloDefinicion
from evidencias.modelos import Evidencia
from evidencias.serializadores import EvidenciaSerializador

from .models import ValorCriterio, ValorModelo, VinculoDato
from .serializadores import ValorCriterioSerializador, ValorModeloSerializador, VinculoDatoSerializador
from .servicios import (
    datos_de_evidencia,
    datos_sin_respaldo,
    desvincular,
    guardar_valor_criterio,
    guardar_valores_modelo,
    vincular,
)


def _validar_permiso(request, accion, *, entidad=None, objeto=None):
    usuario = getattr(request, "user", None)
    if usuario is None or not getattr(usuario, "is_authenticated", False):
        raise PermissionDenied("Se requiere autenticación para operar con datos cuantitativos.")
    if not puede(usuario, accion, objeto=objeto):
        raise PermisoSistema(
            "No tiene permiso para realizar esta acción.",
            accion=accion,
            entidad=entidad or "DatoCuantitativo",
        )


def _normalizar_json_number(valor):
    if isinstance(valor, Decimal):
        valor = float(valor)
        if valor.is_integer():
            return int(valor)
        return valor
    if isinstance(valor, str):
        try:
            numeral = Decimal(valor)
        except Exception:
            return valor
        valor = float(numeral)
        if valor.is_integer():
            return int(valor)
        return valor
    return valor


def _serializar_valor_modelo(obj):
    datos = ValorModeloSerializador(obj).data
    datos = {k: _normalizar_json_number(v) for k, v in datos.items()}
    return {**datos, "valor_modelo": obj.pk, "dato": {**datos}}


def _serializar_valor_criterio(obj):
    datos = ValorCriterioSerializador(obj).data
    datos = {k: _normalizar_json_number(v) for k, v in datos.items()}
    return {**datos, "valor_criterio": obj.pk, "dato": {**datos}}


def _serializar_evidencia(obj):
    return EvidenciaSerializador(obj).data


def _coerce_decimal_nullable(value):
    if value in (None, ""):
        return None
    return value


def _resolver_dato_payload(payload, *, default_tipo=None):
    if payload is None:
        raise ValueError("Debe indicar el dato cuantitativo a asociar.")
    if isinstance(payload, dict):
        tipo = payload.get("tipo") or payload.get("dato_tipo") or payload.get("tipo_dato") or default_tipo
        dato_id = payload.get("id") or payload.get("dato_id") or payload.get("valor_modelo_id") or payload.get("valor_criterio_id")
        if dato_id is None:
            if "valor_modelo" in payload:
                return payload["valor_modelo"], "modelo"
            if "valor_criterio" in payload:
                return payload["valor_criterio"], "criterio"
        return dato_id, tipo
    return payload, default_tipo


class CicloValoresModeloVista(APIView):
    permission_classes = (AllowAny,)

    def get_ciclo(self):
        return get_object_or_404(Ciclo.objects.select_related("version_normativa", "carrera"), pk=self.kwargs["pk"])

    def get_modelo(self):
        return get_object_or_404(
            ModeloDefinicion.objects.select_related("version").prefetch_related("campos"),
            numero=self.kwargs["modelo_num"],
            version=self.get_ciclo().version_normativa,
        )

    def get(self, request, pk, modelo_num):
        ciclo = self.get_ciclo()
        _validar_permiso(request, "crear_valoracion", entidad="ValorModelo", objeto=ciclo)
        modelo = self.get_modelo()
        curso = request.query_params.get("curso")
        queryset = ValorModelo.objects.filter(ciclo=ciclo, campo__modelo=modelo).select_related("campo", "campo__modelo")
        if curso not in (None, ""):
            queryset = queryset.filter(curso=int(curso))
        valores = [_serializar_valor_modelo(item) for item in queryset.order_by("campo__orden", "pk")]
        return Response({
            "ciclo": ciclo.pk,
            "modelo": modelo.numero,
            "curso": int(curso) if curso not in (None, "") else None,
            "valores": valores,
            "celdas": valores,
        })

    def put(self, request, pk, modelo_num):
        ciclo = self.get_ciclo()
        _validar_permiso(request, "editar_valoracion", entidad="ValorModelo", objeto=ciclo)
        modelo = self.get_modelo()
        curso = request.query_params.get("curso") or request.data.get("curso")
        if curso in (None, ""):
            return Response({"detalle": "Debe indicar el curso de la valoración."}, status=400)
        celdas = request.data.get("celdas")
        if celdas is None:
            celdas = request.data.get("valores")
        if celdas is None:
            celdas = request.data.get("datos")
        if celdas is None:
            celdas = request.data
        registros = guardar_valores_modelo(ciclo, modelo, curso, celdas, usuario=request.user)
        valores = [_serializar_valor_modelo(item) for item in registros]
        return Response({
            "ciclo": ciclo.pk,
            "modelo": modelo.numero,
            "curso": int(curso),
            "valores": valores,
            "celdas": valores,
        })


class CicloValorCriterioVista(APIView):
    permission_classes = (AllowAny,)

    def get_ciclo(self):
        return get_object_or_404(Ciclo.objects.select_related("version_normativa", "carrera"), pk=self.kwargs["pk"])

    def get_criterio(self, ciclo):
        return get_object_or_404(
            Criterio.objects.select_related("indicador__dimension__version"),
            codigo=self.kwargs["codigo"],
            indicador__dimension__version=ciclo.version_normativa,
        )

    def get(self, request, pk, codigo):
        ciclo = self.get_ciclo()
        _validar_permiso(request, "crear_valoracion", entidad="ValorCriterio", objeto=ciclo)
        criterio = self.get_criterio(ciclo)
        valor = ValorCriterio.objects.filter(ciclo=ciclo, criterio=criterio).select_related("criterio").first()
        respuesta = _serializar_valor_criterio(valor) if valor is not None else {
            "id": None,
            "tipo": "criterio",
            "criterio": criterio.pk,
            "codigo": criterio.codigo,
            "curso": None,
            "valor": None,
            "numerador": None,
            "denominador": None,
            "unidad": "",
            "observacion": "",
            "dato": {
                "id": None,
                "tipo": "criterio",
                "criterio": criterio.pk,
                "codigo": criterio.codigo,
                "curso": None,
                "valor": None,
                "numerador": None,
                "denominador": None,
                "unidad": "",
                "observacion": "",
            },
        }
        return Response({
            "ciclo": ciclo.pk,
            "criterio": criterio.codigo,
            "valor": respuesta,
            "dato": respuesta,
        })

    def put(self, request, pk, codigo):
        ciclo = self.get_ciclo()
        _validar_permiso(request, "editar_valoracion", entidad="ValorCriterio", objeto=ciclo)
        criterio = self.get_criterio(ciclo)
        datos = request.data.copy()
        valor = guardar_valor_criterio(
            ciclo,
            criterio,
            valor=datos.get("valor"),
            numerador=datos.get("numerador"),
            denominador=datos.get("denominador"),
            curso=datos.get("curso"),
            unidad=datos.get("unidad") or datos.get("unidades") or "",
            observacion=datos.get("observacion") or "",
            usuario=request.user,
        )
        respuesta = _serializar_valor_criterio(valor)
        return Response({
            "ciclo": ciclo.pk,
            "criterio": criterio.codigo,
            "valor": respuesta,
            "dato": respuesta,
        })


class VinculoDatoVista(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        data = request.data
        evidencia_id = data.get("evidencia") or data.get("evidencia_id") or data.get("evidenciaPk")
        if evidencia_id is None:
            return Response({"detalle": "Debe indicar la evidencia."}, status=400)
        dato_id, tipo = _resolver_dato_payload(data.get("dato"), default_tipo=data.get("dato_tipo") or data.get("tipo_dato") or data.get("tipo"))
        if dato_id is None:
            if "valor_modelo" in data:
                dato_id = data["valor_modelo"]
                tipo = "modelo"
            elif "valor_criterio" in data:
                dato_id = data["valor_criterio"]
                tipo = "criterio"
            elif "dato_id" in data:
                dato_id = data["dato_id"]
                tipo = data.get("dato_tipo") or data.get("tipo")
        if dato_id is None:
            return Response({"detalle": "Debe indicar el dato cuantitativo."}, status=400)
        if tipo in ("modelo", "valor_modelo", "valormodelo", "modelo_resumen"):
            dato = dato_id
            _validar_permiso(request, "editar_valoracion", entidad="VinculoDato", objeto=ValorModelo.objects.filter(pk=dato).first())
            if not ValorModelo.objects.filter(pk=dato).exists():
                return Response({"detalle": "No existe el valor de modelo indicado."}, status=404)
        elif tipo in ("criterio", "valor_criterio", "valorcriterio"):
            dato = dato_id
            _validar_permiso(request, "editar_valoracion", entidad="VinculoDato", objeto=ValorCriterio.objects.filter(pk=dato).first())
            if not ValorCriterio.objects.filter(pk=dato).exists():
                return Response({"detalle": "No existe el valor de criterio indicado."}, status=404)
        else:
            return Response({"detalle": "El tipo de dato no es válido."}, status=400)

        enlaces = vincular(dato, [evidencia_id], usuario=request.user)
        return Response({
            "ok": True,
            "vinculos": [VinculoDatoSerializador(enlace).data for enlace in enlaces],
        }, status=201)

    def delete(self, request):
        data = request.data
        evidencia_id = data.get("evidencia") or data.get("evidencia_id")
        if evidencia_id is None:
            return Response({"detalle": "Debe indicar la evidencia."}, status=400)
        dato_id, tipo = _resolver_dato_payload(data.get("dato"), default_tipo=data.get("dato_tipo") or data.get("tipo_dato") or data.get("tipo"))
        if dato_id is None:
            return Response({"detalle": "Debe indicar el dato cuantitativo."}, status=400)
        if tipo in ("modelo", "valor_modelo", "valormodelo"):
            _validar_permiso(request, "editar_valoracion", entidad="VinculoDato", objeto=ValorModelo.objects.filter(pk=dato_id).first())
            total = desvincular(dato_id, [evidencia_id], usuario=request.user)
        elif tipo in ("criterio", "valor_criterio", "valorcriterio"):
            _validar_permiso(request, "editar_valoracion", entidad="VinculoDato", objeto=ValorCriterio.objects.filter(pk=dato_id).first())
            total = desvincular(dato_id, [evidencia_id], usuario=request.user)
        else:
            return Response({"detalle": "El tipo de dato no es válido."}, status=400)
        return Response({"ok": True, "eliminados": total}, status=204)


class DatosEvidenciaVista(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, pk):
        evidencia = get_object_or_404(Evidencia.objects.select_related("ciclo"), pk=pk)
        _validar_permiso(request, "crear_valoracion", entidad="Evidencia", objeto=evidencia)
        datos = datos_de_evidencia(evidencia)
        resultado = []
        for item in datos:
            if isinstance(item, ValorModelo):
                resultado.append(_serializar_valor_modelo(item))
            else:
                resultado.append(_serializar_valor_criterio(item))
        return Response({"evidencia": evidencia.pk, "datos": resultado})


class EvidenciasDatoVista(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, tipo, pk):
        tipo_normalizado = str(tipo).strip().lower()
        if tipo_normalizado in ("modelo", "valormodelo", "valor_modelo"):
            dato = get_object_or_404(ValorModelo.objects.select_related("ciclo", "campo__modelo"), pk=pk)
            _validar_permiso(request, "crear_valoracion", entidad="ValorModelo", objeto=dato.ciclo)
            relaciones = VinculoDato.objects.filter(valor_modelo=dato).select_related("evidencia")
        elif tipo_normalizado in ("criterio", "valorcriterio", "valor_criterio"):
            dato = get_object_or_404(ValorCriterio.objects.select_related("ciclo", "criterio"), pk=pk)
            _validar_permiso(request, "crear_valoracion", entidad="ValorCriterio", objeto=dato.ciclo)
            relaciones = VinculoDato.objects.filter(valor_criterio=dato).select_related("evidencia")
        else:
            return Response({"detalle": "El tipo de dato no es válido."}, status=400)
        evidencias = [relacion.evidencia for relacion in relaciones]
        return Response({
            "tipo": tipo_normalizado,
            "dato": pk,
            "evidencias": [ _serializar_evidencia(item) for item in evidencias ],
        })


class DatosSinRespaldoCicloVista(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, pk):
        ciclo = get_object_or_404(Ciclo.objects.select_related("version_normativa", "carrera"), pk=pk)
        _validar_permiso(request, "crear_valoracion", entidad="Ciclo", objeto=ciclo)
        datos = datos_sin_respaldo(ciclo)
        resultado = []
        for item in datos:
            if isinstance(item, ValorModelo):
                resultado.append(_serializar_valor_modelo(item))
            else:
                resultado.append(_serializar_valor_criterio(item))
        return Response({"ciclo": ciclo.pk, "datos_sin_respaldo": resultado, "datos": resultado})


__all__ = [
    "CicloValoresModeloVista",
    "CicloValorCriterioVista",
    "VinculoDatoVista",
    "DatosEvidenciaVista",
    "EvidenciasDatoVista",
    "DatosSinRespaldoCicloVista",
]
