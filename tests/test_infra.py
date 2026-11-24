"""Documentação, cabeçalhos de segurança, HTTPS e respostas de erro internas."""
import pytest
from rest_framework.test import APIClient

from .helpers import verificar_erro

pytestmark = pytest.mark.django_db


def test_health_check(api):
    """[Hospedagem] Verificação de disponibilidade
    Esperado: HTTP 200 {"status": "ok"} sem autenticação."""
    r = api.get("/api/saude")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


def test_swagger_ui_e_redoc_disponiveis(api):
    """[Hospedagem] Documentação online (Swagger UI e ReDoc)
    Esperado: HTTP 200 em /api/docs e /api/redoc."""
    assert api.get("/api/docs").status_code == 200
    assert api.get("/api/redoc").status_code == 200


def test_esquema_openapi_completo(api):
    """[Hospedagem] Esquema OpenAPI publicado em /api/schema
    Esperado: HTTP 200, esquema de segurança Bearer JWT e todos os endpoints documentados."""
    r = api.get("/api/schema", HTTP_ACCEPT="application/json")
    assert r.status_code == 200
    esquema = r.json()
    assert "jwtAuth" in esquema["components"]["securitySchemes"]
    esperados = {
        "/api/auth/cadastro", "/api/auth/login", "/api/auth/refresh", "/api/auth/logout",
        "/api/auth/esqueci-senha", "/api/auth/redefinir-senha", "/api/usuarios/me",
        "/api/mensagens", "/api/mensagens/{id}", "/api/depoimentos", "/api/depoimentos/{id}",
        "/api/admin/usuarios", "/api/admin/usuarios/{id}", "/api/admin/logins",
        "/api/admin/logins/resumo", "/api/saude",
    }
    assert esperados <= set(esquema["paths"])
    # Toda operação precisa ter resumo e descrição de respostas.
    for caminho, metodos in esquema["paths"].items():
        for metodo, op in metodos.items():
            assert op.get("summary") and op.get("responses"), f"{metodo.upper()} {caminho}"


def test_swagger_marca_rotas_protegidas(api):
    """[Hospedagem] Documentação indica quais rotas exigem autenticação
    Esperado: /usuarios/me exige jwtAuth; /auth/login não exige."""
    paths = api.get("/api/schema", HTTP_ACCEPT="application/json").json()["paths"]
    assert {"jwtAuth": []} in paths["/api/usuarios/me"]["get"]["security"]
    # No OpenAPI, "security": [{}] significa acesso anônimo permitido.
    assert paths["/api/auth/login"]["post"]["security"] == [{}]


def test_cabecalhos_de_seguranca(api):
    """[Hospedagem] Cabeçalhos de segurança nas respostas
    Esperado: X-Content-Type-Options=nosniff e X-Frame-Options=DENY."""
    r = api.get("/api/saude")
    assert r["X-Content-Type-Options"] == "nosniff" and r["X-Frame-Options"] == "DENY"


def test_redireciona_http_para_https(settings):
    """[Hospedagem] Requisição HTTP quando o redirecionamento para HTTPS está ativo
    Esperado: HTTP 301 para o endereço https://."""
    settings.SECURE_SSL_REDIRECT = True
    r = APIClient().get("/api/depoimentos", secure=False)
    assert r.status_code == 301 and r["Location"].startswith("https://")


def test_https_atras_do_proxy_nao_redireciona(settings):
    """[Hospedagem] Requisição que chegou por HTTPS ao proxy (X-Forwarded-Proto: https)
    Esperado: HTTP 200 (sem laço de redirecionamento)."""
    settings.SECURE_SSL_REDIRECT = True
    r = APIClient().get("/api/depoimentos", secure=False, HTTP_X_FORWARDED_PROTO="https")
    assert r.status_code == 200


def test_health_check_nao_e_redirecionado(settings):
    """[Hospedagem] Health check do provedor chega por HTTP interno
    Esperado: HTTP 200 mesmo com redirecionamento para HTTPS ativo (rota isenta)."""
    settings.SECURE_SSL_REDIRECT = True
    assert APIClient().get("/api/saude", secure=False).status_code == 200


def test_erro_interno_nao_vaza_detalhes(monkeypatch):
    """[Hospedagem] Erro inesperado no servidor
    Esperado: HTTP 500 com mensagem genérica, sem traceback nem texto da exceção."""
    from common.views import SaudeView

    def quebrar(self, request):
        raise RuntimeError("segredo-interno-do-banco")

    monkeypatch.setattr(SaudeView, "get", quebrar)
    cliente = APIClient(raise_request_exception=False)
    r = cliente.get("/api/saude")
    verificar_erro(r, 500)
    assert b"segredo-interno" not in r.content and b"Traceback" not in r.content


def test_admin_do_django_fora_do_caminho_padrao(api):
    """[Hospedagem] Painel do Django não fica no endereço previsível /admin/
    Esperado: /admin/ retorna 404; o caminho configurado (ADMIN_URL) existe."""
    assert api.get("/admin/").status_code == 404
    assert api.get("/painel-admin/").status_code in (200, 302)
