"""Rotas principais. Todas as rotas da API ficam sob o prefixo /api/."""
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from common.views import SaudeView

handler404 = "common.views.erro_404"
handler500 = "common.views.erro_500"

urlpatterns = [
    path("", RedirectView.as_view(url="/api/docs", permanent=False)),
    path(settings.ADMIN_URL, admin.site.urls),
    # Documentação (Swagger UI, ReDoc e esquema OpenAPI)
    path("api/schema", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # Sistema
    path("api/saude", SaudeView.as_view(), name="saude"),
    # Domínios
    path("api/", include("contas.urls")),
    path("api/", include("mensagens.urls")),
    path("api/", include("depoimentos.urls")),
]
