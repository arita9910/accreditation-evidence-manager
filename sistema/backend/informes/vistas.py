import mimetypes
from pathlib import Path, PureWindowsPath

from django.conf import settings
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from auditoria.servicios import registrar
from ciclos.modelos import Ciclo
from cuentas.permisos import PermisoSistema, puede
from evidencias.modelos import Evidencia, FicheroEvidencia
from evidencias.serializadores import EvidenciaSerializador
from nucleo import almacenamiento

from .modelos import (
    SECCIONES_INFORME_DOCUMENTADAS,
    TextoInforme,
    VersionInforme,
)
from .serializadores import (
    TextoInformeActualizarSerializador,
    TextoInformeSerializador,
    VersionInformeSerializador,
)
from .servicios import generar_version, guardar_texto


def _validar_permiso(request, accion, *, entidad=None, objeto=None):
    usuario = getattr(request, "user", None)
    if usuario is None or not getattr(usuario, "is_authenticated", False):
        raise PermisoSistema(
            "Debe autenticarse.",
            accion=accion,
            entidad=entidad or "Recurso",
        )
    if not puede(usuario, accion, objeto=objeto):
        request.accion_denegada = accion
        request.entidad_denegada = entidad or "Recurso"
        raise PermisoSistema(
            "No tiene permiso para realizar esta acción.",
            accion=accion,
            entidad=entidad or "Recurso",
        )


class GenerarInformeVista(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, pk):
        ciclo = get_object_or_404(Ciclo, pk=pk)
        _validar_permiso(
            request,
            "generar_informe",
            entidad="VersionInforme",
            objeto=ciclo,
        )
        version = generar_version(ciclo, request.user)
        return Response(
            VersionInformeSerializador(version).data,
            status=status.HTTP_201_CREATED,
        )


class TextosInformeListaVista(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, pk):
        ciclo = get_object_or_404(Ciclo, pk=pk)
        _validar_permiso(
            request,
            "consultar_informe",
            entidad="TextoInforme",
            objeto=ciclo,
        )
        textos = {
            texto.seccion: TextoInformeSerializador(texto).data
            for texto in TextoInforme.objects.filter(ciclo=ciclo)
        }
        return Response(
            {
                "ciclo": ciclo.pk,
                "secciones": [
                    {
                        "seccion": seccion,
                        "descripcion": descripcion,
                        "contenido": (
                            textos.get(seccion, {}).get("contenido", "")
                        ),
                        "texto": textos.get(seccion),
                    }
                    for seccion, descripcion in SECCIONES_INFORME_DOCUMENTADAS.items()
                ],
            }
        )


class TextoInformeSeccionVista(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, pk, seccion):
        ciclo = get_object_or_404(Ciclo, pk=pk)
        _validar_permiso(
            request,
            "consultar_informe",
            entidad="TextoInforme",
            objeto=ciclo,
        )
        if seccion not in SECCIONES_INFORME_DOCUMENTADAS:
            raise serializers.ValidationError(
                {"seccion": "La sección del informe no es válida."}
            )
        texto = TextoInforme.objects.filter(ciclo=ciclo, seccion=seccion).first()
        if texto is None:
            return Response(
                {
                    "ciclo": ciclo.pk,
                    "seccion": seccion,
                    "contenido": "",
                }
            )
        return Response(TextoInformeSerializador(texto).data)

    def put(self, request, pk, seccion):
        ciclo = get_object_or_404(Ciclo, pk=pk)
        _validar_permiso(
            request,
            "guardar_texto_informe",
            entidad="TextoInforme",
            objeto=ciclo,
        )
        serializador = TextoInformeActualizarSerializador(data=request.data)
        serializador.is_valid(raise_exception=True)
        texto = guardar_texto(
            ciclo,
            seccion,
            serializador.validated_data["contenido"],
            request.user,
        )
        return Response(TextoInformeSerializador(texto).data)


class VersionesInformeListaVista(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, pk):
        ciclo = get_object_or_404(Ciclo, pk=pk)
        _validar_permiso(
            request,
            "consultar_informe",
            entidad="VersionInforme",
            objeto=ciclo,
        )
        versiones = VersionInforme.objects.filter(ciclo=ciclo).order_by("-numero")
        if getattr(request.user, "rol", None) == "par_evaluador":
            final = versiones.first()
            versiones = versiones.filter(pk=final.pk) if final is not None else versiones.none()
        return Response(
            {
                "ciclo": ciclo.pk,
                "versiones": VersionInformeSerializador(versiones, many=True).data,
            }
        )


class DescargarVersionInformeVista(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, pk):
        version = get_object_or_404(VersionInforme.objects.select_related("ciclo"), pk=pk)
        _validar_permiso(
            request,
            "descargar_informe",
            entidad="VersionInforme",
            objeto=version.ciclo,
        )
        if getattr(request.user, "rol", None) == "par_evaluador":
            final = (
                VersionInforme.objects.filter(ciclo=version.ciclo)
                .order_by("-numero")
                .first()
            )
            if final is None or final.pk != version.pk:
                request.accion_denegada = "descargar_informe"
                request.entidad_denegada = "VersionInforme"
                raise PermisoSistema(
                    "El par evaluador solo puede descargar la versión final.",
                    accion="descargar_informe",
                    entidad="VersionInforme",
                )

        archivo = almacenamiento.abrir_fichero(version.fichero)
        registrar(
            "descargar_informe",
            usuario=request.user,
            entidad="VersionInforme",
            detalle={
                "id": version.pk,
                "ciclo_id": version.ciclo_id,
                "numero": version.numero,
                "sha256": version.sha256,
            },
            contexto={"ciclo_id": version.ciclo_id},
        )
        nombre = f"informe-ciclo-{version.ciclo_id}-v{version.numero}.docx"
        response = FileResponse(
            archivo,
            as_attachment=True,
            filename=nombre,
        )
        response["Content-Type"] = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        return response


class ExpedienteCicloVista(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, pk):
        ciclo = get_object_or_404(Ciclo, pk=pk)
        _validar_permiso(
            request,
            "consultar_expediente",
            entidad="Expediente",
            objeto=ciclo,
        )
        evidencias = (
            Evidencia.objects.filter(ciclo=ciclo)
            .select_related("tipo_evidencia")
            .prefetch_related("clasificaciones__criterio", "ficheros")
            .order_by("tipo_evidencia__dimension__orden", "tipo_evidencia__nombre", "titulo")
        )
        registrar(
            "consultar_expediente",
            usuario=request.user,
            entidad="Expediente",
            detalle={"ciclo_id": ciclo.pk, "total_evidencias": evidencias.count()},
            contexto={"ciclo_id": ciclo.pk},
        )
        return Response(
            {
                "ciclo": ciclo.pk,
                "evidencias": EvidenciaSerializador(evidencias, many=True).data,
            }
        )


class DescargarFicheroExpedienteVista(APIView):
    permission_classes = (AllowAny,)

    def get(self, request, pk, fichero_id):
        ciclo = get_object_or_404(Ciclo, pk=pk)
        fichero = get_object_or_404(
            FicheroEvidencia.objects.select_related("evidencia"),
            pk=fichero_id,
        )
        if fichero.evidencia.ciclo_id != ciclo.pk:
            request.accion_denegada = "descargar_expediente"
            request.entidad_denegada = "FicheroEvidencia"
            raise PermisoSistema(
                "El fichero no pertenece al ciclo solicitado.",
                accion="descargar_expediente",
                entidad="FicheroEvidencia",
            )
        _validar_permiso(
            request,
            "descargar_expediente",
            entidad="FicheroEvidencia",
            objeto=ciclo,
        )

        extension = PureWindowsPath(fichero.nombre_original).suffix
        ruta = (
            Path(settings.EVIDENCIAS_ROOT)
            / "ciclos"
            / str(fichero.evidencia_id)
            / "evidencias"
            / f"{fichero.nombre_interno}{extension or ''}"
        )
        if not ruta.is_file():
            raise FileNotFoundError("El fichero solicitado no existe.")

        registrar(
            "descargar_expediente",
            usuario=request.user,
            entidad="FicheroEvidencia",
            detalle={
                "ciclo_id": ciclo.pk,
                "evidencia_id": fichero.evidencia_id,
                "fichero_id": fichero.pk,
                "nombre_original": fichero.nombre_original,
            },
            contexto={"ciclo_id": ciclo.pk},
        )
        response = FileResponse(
            ruta.open("rb"),
            as_attachment=True,
            filename=fichero.nombre_original,
        )
        response["Content-Type"] = (
            fichero.tipo_mime
            or mimetypes.guess_type(fichero.nombre_original)[0]
            or "application/octet-stream"
        )
        return response
