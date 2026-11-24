"""Administração (somente ADMIN) e dados do próprio usuário (/usuarios/me)."""
from datetime import timedelta

import pytest
from django.utils import timezone

from contas.models import HistoricoLogin, Usuario
from mensagens.models import Mensagem

from .helpers import verificar_erro

pytestmark = pytest.mark.django_db


# ------------------------------------------------------------ autorização
@pytest.mark.parametrize("caminho", ["/api/admin/usuarios", "/api/admin/logins", "/api/admin/logins/resumo"])
def test_rotas_admin_sem_token(api, caminho):
    """[Autenticação] Rotas administrativas sem token
    Esperado: HTTP 401."""
    verificar_erro(api.get(caminho), 401)


@pytest.mark.parametrize("caminho", ["/api/admin/usuarios", "/api/admin/logins", "/api/admin/logins/resumo"])
def test_rotas_admin_com_usuario_comum(api_usuario, caminho):
    """[Autorização] Usuário comum tenta acessar rota administrativa
    Esperado: HTTP 403."""
    verificar_erro(api_usuario.get(caminho), 403)


# ---------------------------------------------------- gestão de usuários
def test_admin_lista_usuarios(api_admin, usuario, outro_usuario):
    """[CRUD] ADMIN lista usuários
    Esperado: HTTP 200 com todos os usuários (3) e sem campo de senha."""
    r = api_admin.get("/api/admin/usuarios")
    assert r.status_code == 200 and r.json()["count"] == 3
    assert all("senha" not in u and "password" not in u for u in r.json()["results"])


def test_admin_filtra_e_busca_usuarios(api_admin, usuario, outro_usuario):
    """[Recursos adicionais] ADMIN filtra por perfil e busca por nome
    Esperado: perfil=ADMIN retorna 1; search=João retorna 1."""
    assert api_admin.get("/api/admin/usuarios?perfil=ADMIN").json()["count"] == 1
    r = api_admin.get("/api/admin/usuarios?search=João").json()
    assert r["count"] == 1 and r["results"][0]["email"] == "joao@email.com"


def test_admin_consulta_usuario(api_admin, usuario):
    """[CRUD] ADMIN consulta um usuário
    Esperado: HTTP 200 (e 404 para id inexistente)."""
    assert api_admin.get(f"/api/admin/usuarios/{usuario.id}").status_code == 200
    verificar_erro(api_admin.get("/api/admin/usuarios/99999"), 404)


def test_admin_promove_usuario(api_admin, usuario):
    """[CRUD] ADMIN altera o perfil de um usuário
    Esperado: HTTP 200 e perfil persistido como ADMIN."""
    r = api_admin.patch(f"/api/admin/usuarios/{usuario.id}", {"perfil": "ADMIN"}, format="json")
    assert r.status_code == 200 and r.json()["perfil"] == "ADMIN"
    usuario.refresh_from_db()
    assert usuario.eh_admin


def test_admin_perfil_inexistente(api_admin, usuario):
    """[Validação] ADMIN informa um perfil que não existe
    Esperado: HTTP 400 com erro em perfil."""
    r = api_admin.patch(f"/api/admin/usuarios/{usuario.id}", {"perfil": "SUPER"}, format="json")
    assert "perfil" in verificar_erro(r, 400)["detalhes"]


def test_admin_nao_altera_email(api_admin, usuario):
    """[Validação] ADMIN tenta alterar o e-mail de um usuário
    Esperado: HTTP 200, mas o e-mail permanece o mesmo (campo somente leitura)."""
    api_admin.patch(f"/api/admin/usuarios/{usuario.id}", {"email": "novo@email.com"}, format="json")
    usuario.refresh_from_db()
    assert usuario.email == "maria@email.com"


def test_admin_nao_rebaixa_a_si_mesmo(api_admin, admin):
    """[Validação] ADMIN tenta rebaixar o próprio perfil
    Esperado: HTTP 400."""
    r = api_admin.patch(f"/api/admin/usuarios/{admin.id}", {"perfil": "USUARIO"}, format="json")
    assert "perfil" in verificar_erro(r, 400)["detalhes"]


def test_admin_desativa_usuario_e_login_falha(api_admin, usuario, api):
    """[Autorização] ADMIN desativa uma conta
    Esperado: HTTP 200 e o usuário não consegue mais fazer login (401)."""
    api_admin.patch(f"/api/admin/usuarios/{usuario.id}", {"is_active": False}, format="json")
    r = api.post("/api/auth/login", {"email": "maria@email.com", "senha": "Senha@Forte2026"}, format="json")
    verificar_erro(r, 401)


def test_admin_exclui_usuario(api_admin, usuario):
    """[CRUD] ADMIN exclui um usuário
    Esperado: HTTP 204 e o usuário (e suas mensagens) somem do banco."""
    Mensagem.objects.create(usuario=usuario, servico="OUTROS", mensagem="x")
    assert api_admin.delete(f"/api/admin/usuarios/{usuario.id}").status_code == 204
    assert not Usuario.objects.filter(id=usuario.id).exists() and Mensagem.objects.count() == 0


def test_admin_nao_exclui_a_si_mesmo(api_admin, admin):
    """[Validação] ADMIN tenta excluir a própria conta pelo endpoint administrativo
    Esperado: HTTP 400 e a conta continua existindo."""
    verificar_erro(api_admin.delete(f"/api/admin/usuarios/{admin.id}"), 400)
    assert Usuario.objects.filter(id=admin.id).exists()


# ------------------------------------------------------ histórico de logins
@pytest.fixture
def historico(usuario):
    agora = timezone.now()
    HistoricoLogin.objects.create(usuario=usuario, status="SUCESSO", ip="1.1.1.1", navegador="Chrome", data_hora=agora - timedelta(days=1))
    HistoricoLogin.objects.create(usuario=usuario, status="SUCESSO", ip="1.1.1.2", navegador="Firefox", data_hora=agora - timedelta(days=2))
    HistoricoLogin.objects.create(usuario=None, status="FALHA", ip="9.9.9.9", navegador="Edge", data_hora=agora - timedelta(days=3))
    HistoricoLogin.objects.create(usuario=usuario, status="SUCESSO", ip="1.1.1.3", data_hora=agora - timedelta(days=60))


def test_admin_lista_historico(api_admin, historico):
    """[CRUD] ADMIN consulta o histórico de logins
    Esperado: HTTP 200 com 4 registros, do mais recente ao mais antigo."""
    r = api_admin.get("/api/admin/logins").json()
    assert r["count"] == 4 and r["results"][0]["ip"] == "1.1.1.1"


def test_admin_filtra_historico_por_status_e_busca(api_admin, historico):
    """[Recursos adicionais] Histórico filtrado por status e buscado por navegador
    Esperado: status=FALHA retorna 1; search=Firefox retorna 1."""
    assert api_admin.get("/api/admin/logins?status=FALHA").json()["count"] == 1
    assert api_admin.get("/api/admin/logins?search=Firefox").json()["count"] == 1


def test_admin_resumo_de_acessos(api_admin, historico):
    """[Recursos adicionais] Indicadores de acesso dos últimos 30 dias
    Esperado: 3 logins no total, 2 sucessos, 1 falha e último acesso preenchido."""
    r = api_admin.get("/api/admin/logins/resumo").json()
    assert (r["total_logins"], r["logins_realizados"], r["falhas_de_login"]) == (3, 2, 1)
    assert r["periodo_dias"] == 30 and r["ultimo_acesso"]


def test_admin_resumo_dias_invalido(api_admin):
    """[Validação] Parâmetro dias fora do intervalo ou não numérico
    Esperado: HTTP 400 com erro em dias."""
    for valor in ("0", "366", "abc"):
        assert "dias" in verificar_erro(api_admin.get(f"/api/admin/logins/resumo?dias={valor}"), 400)["detalhes"]


def test_historico_nao_aceita_escrita(api_admin):
    """[Autorização] Tentar criar registro de histórico pela API
    Esperado: HTTP 405 (o histórico só é gravado pelo login)."""
    verificar_erro(api_admin.post("/api/admin/logins", {"status": "SUCESSO"}, format="json"), 405)


# ------------------------------------------------------------ /usuarios/me
def test_consultar_proprio_perfil(api_usuario):
    """[CRUD] Consultar o próprio cadastro
    Esperado: HTTP 200 com os dados (sem senha)."""
    r = api_usuario.get("/api/usuarios/me")
    assert r.status_code == 200 and "senha" not in r.json() and "password" not in r.json()


def test_atualizar_proprio_cadastro(api_usuario, usuario):
    """[CRUD] Atualizar o próprio cadastro (PUT e PATCH)
    Esperado: HTTP 200; e-mail e perfil não mudam mesmo se enviados."""
    r = api_usuario.put("/api/usuarios/me", {"nome": "Maria S.", "telefone": "(61) 98888-7777", "perfil": "ADMIN", "email": "x@y.com"}, format="json")
    assert r.status_code == 200
    r = api_usuario.patch("/api/usuarios/me", {"nome": "Maria Souza Lima"}, format="json")
    assert r.status_code == 200
    usuario.refresh_from_db()
    assert usuario.nome == "Maria Souza Lima" and usuario.telefone == "(61) 98888-7777"
    assert usuario.email == "maria@email.com" and not usuario.eh_admin


def test_excluir_propria_conta(api_usuario, usuario):
    """[CRUD] Excluir a própria conta
    Esperado: HTTP 204; usuário e mensagens removidos; histórico de logins mantido sem vínculo."""
    Mensagem.objects.create(usuario=usuario, servico="OUTROS", mensagem="x")
    h = HistoricoLogin.objects.create(usuario=usuario, status="SUCESSO")
    assert api_usuario.delete("/api/usuarios/me").status_code == 204
    assert not Usuario.objects.filter(id=usuario.id).exists() and Mensagem.objects.count() == 0
    h.refresh_from_db()
    assert h.usuario is None
