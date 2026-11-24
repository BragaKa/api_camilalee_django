"""CRUD de mensagens, isolamento entre usuários e recursos de consulta."""
from datetime import timedelta

import pytest
from django.utils import timezone

from mensagens.models import Mensagem

from .helpers import verificar_erro

pytestmark = pytest.mark.django_db

NOVA = {"servico": "NOIVAS", "mensagem": "Quero um orçamento para 14/03."}


@pytest.fixture
def msg(usuario):
    return Mensagem.objects.create(usuario=usuario, servico="NOIVAS", mensagem="Mensagem da Maria")


@pytest.fixture
def msg_outro(outro_usuario):
    return Mensagem.objects.create(usuario=outro_usuario, servico="OUTROS", mensagem="Mensagem do João")


# ------------------------------------------------------------------- CRUD
def test_criar_mensagem(api_usuario, usuario):
    """[CRUD] Criar mensagem autenticado
    Esperado: HTTP 201; remetente é o usuário logado e a mensagem fica gravada no banco."""
    r = api_usuario.post("/api/mensagens", NOVA, format="json")
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["usuario_id"] == usuario.id and corpo["servico"] == "NOIVAS"
    assert Mensagem.objects.get(id=corpo["id"]).mensagem == NOVA["mensagem"]


def test_criar_mensagem_ignora_usuario_enviado(api_usuario, usuario, outro_usuario):
    """[Autorização] Enviar mensagem tentando se passar por outro usuário
    Esperado: HTTP 201, mas o remetente continua sendo o usuário autenticado."""
    r = api_usuario.post("/api/mensagens", {**NOVA, "usuario": outro_usuario.id, "usuario_id": outro_usuario.id}, format="json")
    assert r.status_code == 201 and r.json()["usuario_id"] == usuario.id


def test_listar_mensagens(api_usuario, msg, msg_outro):
    """[CRUD] Listar mensagens
    Esperado: HTTP 200 paginado, contendo apenas as mensagens do próprio usuário."""
    r = api_usuario.get("/api/mensagens")
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["count"] == 1 and corpo["results"][0]["id"] == msg.id


def test_consultar_mensagem(api_usuario, msg):
    """[CRUD] Consultar uma mensagem pelo id
    Esperado: HTTP 200 com os dados da mensagem."""
    r = api_usuario.get(f"/api/mensagens/{msg.id}")
    assert r.status_code == 200 and r.json()["mensagem"] == "Mensagem da Maria"


def test_atualizar_mensagem_completa(api_usuario, msg):
    """[CRUD] Atualizar mensagem (PUT)
    Esperado: HTTP 200 e novos valores persistidos no banco."""
    r = api_usuario.put(f"/api/mensagens/{msg.id}", {"servico": "AUDIOVISUAL", "mensagem": "Texto novo"}, format="json")
    assert r.status_code == 200
    msg.refresh_from_db()
    assert (msg.servico, msg.mensagem) == ("AUDIOVISUAL", "Texto novo")


def test_atualizar_mensagem_parcial(api_usuario, msg):
    """[CRUD] Atualizar mensagem parcialmente (PATCH)
    Esperado: HTTP 200; muda só o campo enviado."""
    r = api_usuario.patch(f"/api/mensagens/{msg.id}", {"servico": "OUTROS"}, format="json")
    assert r.status_code == 200
    msg.refresh_from_db()
    assert msg.servico == "OUTROS" and msg.mensagem == "Mensagem da Maria"


def test_excluir_mensagem(api_usuario, msg):
    """[CRUD] Excluir mensagem
    Esperado: HTTP 204; consulta posterior retorna 404 e o registro some do banco."""
    assert api_usuario.delete(f"/api/mensagens/{msg.id}").status_code == 204
    verificar_erro(api_usuario.get(f"/api/mensagens/{msg.id}"), 404)
    assert not Mensagem.objects.filter(id=msg.id).exists()


# ------------------------------------------------------------ autorização
def test_mensagens_exigem_autenticacao(api, msg):
    """[Autenticação] Acessar mensagens sem token
    Esperado: HTTP 401 em listar, criar, consultar e excluir."""
    for resposta in (
        api.get("/api/mensagens"),
        api.post("/api/mensagens", NOVA, format="json"),
        api.get(f"/api/mensagens/{msg.id}"),
        api.delete(f"/api/mensagens/{msg.id}"),
    ):
        verificar_erro(resposta, 401)


def test_usuario_nao_ve_mensagem_de_outro(api_usuario, msg_outro):
    """[Autorização] Usuário comum tenta consultar mensagem de outro usuário
    Esperado: HTTP 404 (não revela que o registro existe)."""
    verificar_erro(api_usuario.get(f"/api/mensagens/{msg_outro.id}"), 404)


def test_usuario_nao_altera_nem_exclui_mensagem_de_outro(api_usuario, msg_outro):
    """[Autorização] Usuário comum tenta alterar e excluir mensagem de outro usuário
    Esperado: HTTP 404 e o registro permanece intacto."""
    verificar_erro(api_usuario.patch(f"/api/mensagens/{msg_outro.id}", {"mensagem": "hack"}, format="json"), 404)
    verificar_erro(api_usuario.delete(f"/api/mensagens/{msg_outro.id}"), 404)
    msg_outro.refresh_from_db()
    assert msg_outro.mensagem == "Mensagem do João"


def test_admin_ve_todas_as_mensagens(api_admin, msg, msg_outro):
    """[Autorização] ADMIN lista mensagens
    Esperado: HTTP 200 com as mensagens de todos os usuários."""
    assert api_admin.get("/api/mensagens").json()["count"] == 2


def test_admin_exclui_mensagem_de_qualquer_usuario(api_admin, msg):
    """[Autorização] ADMIN exclui mensagem de outro usuário
    Esperado: HTTP 204."""
    assert api_admin.delete(f"/api/mensagens/{msg.id}").status_code == 204


# --------------------------------------------- filtros, busca, ordenação...
@pytest.fixture
def varias(usuario):
    agora = timezone.now()
    dados = [
        ("NOIVAS", "Orçamento de noiva para março", 10),
        ("AUDIOVISUAL", "Maquiagem para gravação de vídeo", 5),
        ("NOIVAS", "Teste de maquiagem de noiva", 1),
        ("OUTROS", "Dúvida sobre produtos", 0),
    ]
    return [
        Mensagem.objects.create(usuario=usuario, servico=s, mensagem=t, enviado_em=agora - timedelta(days=d))
        for s, t, d in dados
    ]


def test_filtrar_por_servico(api_usuario, varias):
    """[Recursos adicionais] Filtrar mensagens por serviço
    Esperado: somente as mensagens do serviço NOIVAS (2)."""
    r = api_usuario.get("/api/mensagens?servico=NOIVAS").json()
    assert r["count"] == 2 and {m["servico"] for m in r["results"]} == {"NOIVAS"}


def test_filtrar_por_periodo(api_usuario, varias):
    """[Recursos adicionais] Filtrar mensagens por período (data_inicio)
    Esperado: apenas as enviadas nos últimos 2 dias (2)."""
    inicio = (timezone.localdate() - timedelta(days=2)).isoformat()
    assert api_usuario.get(f"/api/mensagens?data_inicio={inicio}").json()["count"] == 2


def test_buscar_por_texto(api_usuario, varias):
    """[Recursos adicionais] Buscar mensagens por texto (search)
    Esperado: apenas as que contêm 'maquiagem' (2)."""
    r = api_usuario.get("/api/mensagens?search=maquiagem").json()
    assert r["count"] == 2


def test_ordenar_mensagens(api_usuario, varias):
    """[Recursos adicionais] Ordenar mensagens por data (ordering)
    Esperado: crescente com 'enviado_em' e decrescente com '-enviado_em'."""
    asc = [m["id"] for m in api_usuario.get("/api/mensagens?ordering=enviado_em").json()["results"]]
    desc = [m["id"] for m in api_usuario.get("/api/mensagens?ordering=-enviado_em").json()["results"]]
    assert asc == desc[::-1] and asc[0] == varias[0].id


def test_paginar_mensagens(api_usuario, varias):
    """[Recursos adicionais] Paginar mensagens (page e page_size)
    Esperado: 2 itens por página, count=4 e links next/previous corretos."""
    p1 = api_usuario.get("/api/mensagens?page_size=2").json()
    assert p1["count"] == 4 and len(p1["results"]) == 2 and p1["next"] and not p1["previous"]
    p2 = api_usuario.get("/api/mensagens?page_size=2&page=2").json()
    assert len(p2["results"]) == 2 and p2["previous"] and not p2["next"]
