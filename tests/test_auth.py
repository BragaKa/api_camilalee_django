"""Autenticação: cadastro, login, tokens, logout e recuperação de senha."""
from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone

from contas.models import CodigoRedefinicaoSenha, HistoricoLogin, Usuario

from .helpers import SENHA, cliente_de, verificar_erro

pytestmark = pytest.mark.django_db

CADASTRO = {
    "nome": "Maria Souza",
    "email": "maria@email.com",
    "telefone": "61999999999",
    "senha": SENHA,
}


def login(api, email="maria@email.com", senha=SENHA, **extra):
    return api.post("/api/auth/login", {"email": email, "senha": senha}, format="json", **extra)


# ---------------------------------------------------------------- cadastro
def test_cadastro_valido(api):
    """[CRUD] Cadastrar usuário com dados válidos
    Esperado: HTTP 201, perfil USUARIO e nenhum campo de senha na resposta."""
    r = api.post("/api/auth/cadastro", CADASTRO, format="json")
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["email"] == "maria@email.com" and corpo["perfil"] == "USUARIO"
    assert "senha" not in corpo and "password" not in corpo


def test_senha_armazenada_com_hash(api, settings):
    """[Autenticação] Senha gravada apenas como hash PBKDF2
    Esperado: valor no banco diferente da senha enviada e com prefixo pbkdf2_sha256."""
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.PBKDF2PasswordHasher"]
    api.post("/api/auth/cadastro", CADASTRO, format="json")
    salvo = Usuario.objects.get(email="maria@email.com").password
    assert salvo != SENHA and salvo.startswith("pbkdf2_sha256$")


def test_cadastro_ignora_perfil_enviado(api):
    """[Autorização] Cliente tenta se cadastrar como ADMIN (escalada de privilégio)
    Esperado: HTTP 201, mas o perfil criado é USUARIO."""
    r = api.post("/api/auth/cadastro", {**CADASTRO, "perfil": "ADMIN", "is_staff": True}, format="json")
    assert r.status_code == 201 and r.json()["perfil"] == "USUARIO"
    assert Usuario.objects.get(email="maria@email.com").is_staff is False


def test_cadastro_email_duplicado(api, usuario):
    """[Validação] Cadastrar e-mail já existente (inclusive com maiúsculas)
    Esperado: HTTP 409 com mensagem de conflito."""
    r = api.post("/api/auth/cadastro", {**CADASTRO, "email": "MARIA@Email.com"}, format="json")
    corpo = verificar_erro(r, 409)
    assert "e-mail" in corpo["mensagem"]


# ------------------------------------------------------------------- login
def test_login_valido(api, usuario):
    """[Autenticação] Login com credenciais válidas
    Esperado: HTTP 200 com tokens access e refresh e dados do usuário."""
    r = login(api)
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["access"] and corpo["refresh"] and corpo["token_type"] == "Bearer"
    assert corpo["usuario"]["email"] == "maria@email.com"


def test_login_senha_errada(api, usuario):
    """[Autenticação] Login com senha incorreta
    Esperado: HTTP 401 com mensagem genérica."""
    corpo = verificar_erro(login(api, senha="SenhaErrada#1"), 401)
    assert corpo["mensagem"] == "E-mail ou senha inválidos."


def test_login_email_inexistente(api):
    """[Autenticação] Login com e-mail que não existe
    Esperado: HTTP 401 com a MESMA mensagem da senha errada (não revela se a conta existe)."""
    corpo = verificar_erro(login(api, email="ninguem@email.com"), 401)
    assert corpo["mensagem"] == "E-mail ou senha inválidos."


def test_login_usuario_inativo(api, criar_usuario):
    """[Autenticação] Login de conta desativada
    Esperado: HTTP 401."""
    criar_usuario(is_active=False)
    verificar_erro(login(api), 401)


def test_login_sem_campos(api):
    """[Validação] Login sem enviar e-mail e senha
    Esperado: HTTP 400 com erros por campo."""
    r = api.post("/api/auth/login", {}, format="json")
    corpo = verificar_erro(r, 400)
    assert set(corpo["detalhes"]) == {"email", "senha"}


def test_login_ignora_token_expirado_no_cabecalho(api, usuario):
    """[Autenticação] Login enviado com um cabeçalho Authorization inválido
    Esperado: HTTP 200 (o login é público e ignora o cabeçalho)."""
    r = login(api, HTTP_AUTHORIZATION="Bearer token.invalido.aqui")
    assert r.status_code == 200


def test_login_limite_de_tentativas(api, usuario):
    """[Autenticação] Muitas tentativas de login seguidas (força bruta)
    Esperado: após 10 tentativas, HTTP 429 com cabeçalho Retry-After."""
    for _ in range(10):
        assert login(api, senha="errada#Senha1").status_code == 401
    r = login(api, senha="errada#Senha1")
    verificar_erro(r, 429)
    assert "Retry-After" in r


def test_login_registra_historico(api, usuario):
    """[Autenticação] Cada tentativa de login é registrada no histórico
    Esperado: um registro SUCESSO e um FALHA, com IP, navegador e sistema do User-Agent."""
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
    login(api, HTTP_USER_AGENT=ua)
    login(api, senha="errada#Senha1", HTTP_USER_AGENT=ua)
    registros = {h.status: h for h in HistoricoLogin.objects.all()}
    assert set(registros) == {"SUCESSO", "FALHA"}
    ok = registros["SUCESSO"]
    assert ok.usuario == usuario and ok.navegador == "Chrome" and ok.sistema_operacional == "Windows"
    assert ok.dispositivo == "Computador" and ok.ip == "127.0.0.1"
    assert registros["FALHA"].usuario == usuario


# ------------------------------------------------------ rota protegida/token
def test_rota_protegida_sem_token(api):
    """[Autenticação] Acessar rota protegida sem token
    Esperado: HTTP 401."""
    verificar_erro(api.get("/api/usuarios/me"), 401)


def test_rota_protegida_token_invalido(api):
    """[Autenticação] Acessar rota protegida com token inválido
    Esperado: HTTP 401."""
    api.credentials(HTTP_AUTHORIZATION="Bearer abc.def.ghi")
    verificar_erro(api.get("/api/usuarios/me"), 401)


def test_rota_protegida_token_valido(api, usuario):
    """[Autenticação] Acessar rota protegida com token válido (obtido pelo login)
    Esperado: HTTP 200 com os dados do próprio usuário."""
    token = login(api).json()["access"]
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    r = api.get("/api/usuarios/me")
    assert r.status_code == 200 and r.json()["email"] == "maria@email.com"


def test_token_expirado(api, usuario, settings):
    """[Autenticação] Token de acesso expirado
    Esperado: HTTP 401."""
    from rest_framework_simplejwt.tokens import AccessToken

    token = AccessToken.for_user(usuario)
    token.set_exp(from_time=timezone.now() - timedelta(hours=2), lifetime=timedelta(minutes=1))
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    verificar_erro(api.get("/api/usuarios/me"), 401)


# ----------------------------------------------------------- refresh/logout
def test_refresh_renova_e_invalida_anterior(api, usuario):
    """[Autenticação] Renovar o token com refresh válido
    Esperado: HTTP 200 com novo par de tokens; reusar o refresh antigo retorna 401."""
    refresh = login(api).json()["refresh"]
    r = api.post("/api/auth/refresh", {"refresh": refresh}, format="json")
    assert r.status_code == 200 and r.json()["access"] and r.json()["refresh"]
    verificar_erro(api.post("/api/auth/refresh", {"refresh": refresh}, format="json"), 401)


def test_refresh_invalido(api):
    """[Autenticação] Renovar com refresh inválido
    Esperado: HTTP 401."""
    verificar_erro(api.post("/api/auth/refresh", {"refresh": "lixo"}, format="json"), 401)


def test_logout_invalida_refresh(api, usuario):
    """[Autenticação] Logout com refresh válido
    Esperado: HTTP 204; depois disso o refresh não funciona mais (401)."""
    dados = login(api).json()
    cliente = cliente_de(usuario)
    r = cliente.post("/api/auth/logout", {"refresh": dados["refresh"]}, format="json")
    assert r.status_code == 204
    verificar_erro(api.post("/api/auth/refresh", {"refresh": dados["refresh"]}, format="json"), 401)


def test_logout_sem_autenticacao(api):
    """[Autenticação] Logout sem estar autenticado
    Esperado: HTTP 401."""
    verificar_erro(api.post("/api/auth/logout", {"refresh": "x"}, format="json"), 401)


def test_logout_refresh_invalido(api_usuario):
    """[Validação] Logout com refresh inválido
    Esperado: HTTP 400 com erro no campo refresh."""
    corpo = verificar_erro(api_usuario.post("/api/auth/logout", {"refresh": "lixo"}, format="json"), 400)
    assert "refresh" in corpo["detalhes"]


# ------------------------------------------------------ recuperação de senha
def pedir_codigo(api, email="maria@email.com"):
    return api.post("/api/auth/esqueci-senha", {"email": email}, format="json")


def redefinir(api, codigo, nova="NovaSenha@2026", email="maria@email.com"):
    return api.post(
        "/api/auth/redefinir-senha",
        {"email": email, "codigo": codigo, "nova_senha": nova},
        format="json",
    )


def test_recuperacao_de_senha_completa(api, usuario):
    """[Autenticação] Recuperar senha com código enviado por e-mail
    Esperado: e-mail enviado com código de 6 dígitos; nova senha funciona, a antiga não;
    o mesmo código não pode ser reutilizado."""
    assert pedir_codigo(api).status_code == 200
    assert len(mail.outbox) == 1
    codigo = CodigoRedefinicaoSenha.objects.get(email="maria@email.com").codigo
    assert len(codigo) == 6 and codigo in mail.outbox[0].body

    assert redefinir(api, codigo).status_code == 200
    assert login(api, senha="NovaSenha@2026").status_code == 200
    assert login(api, senha=SENHA).status_code == 401
    verificar_erro(redefinir(api, codigo, nova="OutraSenha@2026"), 400)


def test_esqueci_senha_nao_revela_existencia(api, usuario):
    """[Autenticação] Pedir código para e-mail inexistente
    Esperado: HTTP 200 com a mesma resposta de um e-mail existente e nenhum e-mail enviado."""
    existente = pedir_codigo(api).json()
    inexistente = pedir_codigo(api, "ninguem@email.com")
    assert inexistente.status_code == 200 and inexistente.json() == existente
    assert len(mail.outbox) == 1  # só o do e-mail existente


def test_codigo_incorreto(api, usuario):
    """[Validação] Redefinir senha com código errado
    Esperado: HTTP 400 'Código inválido ou expirado.'"""
    pedir_codigo(api)
    real = CodigoRedefinicaoSenha.objects.get().codigo
    errado = "000000" if real != "000000" else "111111"
    corpo = verificar_erro(redefinir(api, errado), 400)
    assert corpo["detalhes"]["codigo"] == ["Código inválido ou expirado."]


def test_codigo_expirado(api, usuario):
    """[Validação] Redefinir senha com código expirado
    Esperado: HTTP 400."""
    pedir_codigo(api)
    registro = CodigoRedefinicaoSenha.objects.get()
    registro.expira_em = timezone.now() - timedelta(minutes=1)
    registro.save()
    verificar_erro(redefinir(api, registro.codigo), 400)


def test_novo_codigo_invalida_o_anterior(api, usuario):
    """[Autenticação] Pedir um segundo código
    Esperado: o primeiro deixa de valer (HTTP 400) e o segundo funciona (HTTP 200)."""
    pedir_codigo(api)
    primeiro = CodigoRedefinicaoSenha.objects.get().codigo
    pedir_codigo(api)
    segundo = CodigoRedefinicaoSenha.objects.filter(utilizado=False).get().codigo
    if primeiro != segundo:
        verificar_erro(redefinir(api, primeiro), 400)
    assert redefinir(api, segundo).status_code == 200


def test_redefinir_com_senha_fraca(api, usuario):
    """[Validação] Redefinir senha com senha fraca
    Esperado: HTTP 400 com erro em nova_senha."""
    pedir_codigo(api)
    codigo = CodigoRedefinicaoSenha.objects.get().codigo
    corpo = verificar_erro(redefinir(api, codigo, nova="12345678"), 400)
    assert "nova_senha" in corpo["detalhes"] or "non_field_errors" in corpo["detalhes"]


def test_redefinir_encerra_sessoes(api, usuario):
    """[Autenticação] Trocar a senha encerra as sessões abertas
    Esperado: refresh emitido antes da troca passa a retornar 401."""
    refresh = login(api).json()["refresh"]
    pedir_codigo(api)
    redefinir(api, CodigoRedefinicaoSenha.objects.get().codigo)
    verificar_erro(api.post("/api/auth/refresh", {"refresh": refresh}, format="json"), 401)
