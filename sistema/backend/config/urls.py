from django.conf import settings
from django.urls import include, path
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib import admin



@extend_schema(
    responses=inline_serializer(
        name="RespuestaSalud",
        fields={"estado": serializers.CharField()},
    )
)
@api_view(["GET"])
@permission_classes([AllowAny])
def salud(request):
    return Response({"estado": "ok"})


urlpatterns = [
    path("api/salud/", salud, name="salud"),
    path("api/auditoria/", include("auditoria.urls")),
    path("api/", include("cuentas.urls")),
    path("api/", include("ciclos.urls")),
    path("api/", include("evidencias.urls")),
    path('admin/', admin.site.urls),
]

if settings.CATALOGO_API_DESARROLLO:
    urlpatterns += [
        path("api/catalogo/", include("estructura.urls")),
    ]

if settings.DEBUG:
    from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

    urlpatterns += [
        path("api/esquema/", SpectacularAPIView.as_view(), name="schema"),
        path(
            "api/docs/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
    ]
