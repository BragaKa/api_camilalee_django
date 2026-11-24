"""CRUD de depoimentos: leitura pública, escrita só para ADMIN."""
import pytest

from depoimentos.models import Depoimento

from .helpers import verificar_erro

pytestmark = pytest.mark.django_db

NOVO = {"nome_autor": "Ana Paula", "profissao": "Noiva", "texto": "Atendimento incrível!"}


@pytest.fixture
def dep():
    return Depoimento.objects.create(**NOVO)


# ------------------------------------------------------------------- CRUD
def test_listar_depoimentos_publico(api, dep):
    """[CRUD] Listar depoimentos sem estar autenticado
    Esperado: HTTP 200 com resultado paginado."""
    r = api.get("/api/depoimentos")
    assert r.status_code == 200 and r.json()["count"] == 1


def test_consultar_depoimento_publico(api, dep):
    """[CRUD] Consultar depoimento sem estar autenticado
    Esperado: HTTP 200 com os dados do depoimento."""
    r = api.get(f"/api/depoimentos/{dep.id}")
    assert r.status_code == 200 and r.json()["nome_autor"] == "Ana Paula"


def test_criar_depoimento_como_admin(api_admin):
    """[CRUD] ADMIN cria depoimento
    Esperado: HTTP 201 e registro gravado no banco."""
    r = api_admin.post("/api/depoimentos", NOVO, format="json")
    assert r.status_code == 201
    assert Depoimento.objects.get(id=r.json()["id"]).texto == NOVO["texto"]


def test_atualizar_depoimento_como_admin(api_admin, dep):
    """[CRUD] ADMIN atualiza depoimento (PUT e PATCH)
    Esperado: HTTP 200 e valores persistidos."""
    r = api_admin.put(f"/api/depoimentos/{dep.id}", {**NOVO, "profissao": "Atriz"}, format="json")
    assert r.status_code == 200
    r = api_admin.patch(f"/api/depoimentos/{dep.id}", {"texto": "Texto revisado"}, format="json")
    assert r.status_code == 200
    dep.refresh_from_db()
    assert dep.profissao == "Atriz" and dep.texto == "Texto revisado"


def test_excluir_depoimento_como_admin(api_admin, dep):
    """[CRUD] ADMIN exclui depoimento
    Esperado: HTTP 204 e consulta posterior retorna 404."""
    assert api_admin.delete(f"/api/depoimentos/{dep.id}").status_code == 204
    verificar_erro(api_admin.get(f"/api/depoimentos/{dep.id}"), 404)


# ------------------------------------------------------------ autorização
def test_criar_depoimento_sem_autenticacao(api):
    """[Autenticação] Criar depoimento sem token
    Esperado: HTTP 401."""
    verificar_erro(api.post("/api/depoimentos", NOVO, format="json"), 401)


def test_usuario_comum_nao_cria_depoimento(api_usuario):
    """[Autorização] Usuário comum (perfil USUARIO) tenta criar depoimento
    Esperado: HTTP 403."""
    corpo = verificar_erro(api_usuario.post("/api/depoimentos", NOVO, format="json"), 403)
    assert "administradores" in corpo["mensagem"]


def test_usuario_comum_nao_altera_nem_exclui(api_usuario, dep):
    """[Autorização] Usuário comum tenta alterar e excluir depoimento
    Esperado: HTTP 403 e o registro permanece."""
    verificar_erro(api_usuario.patch(f"/api/depoimentos/{dep.id}", {"texto": "x"}, format="json"), 403)
    verificar_erro(api_usuario.delete(f"/api/depoimentos/{dep.id}"), 403)
    assert Depoimento.objects.filter(id=dep.id).exists()


# --------------------------------------------- filtros, busca, ordenação...
@pytest.fixture
def varios():
    return [
        Depoimento.objects.create(nome_autor="Ana", profissao="Noiva", texto="Linda maquiagem"),
        Depoimento.objects.create(nome_autor="Bia", profissao="Atriz", texto="Caracterização perfeita"),
        Depoimento.objects.create(nome_autor="Carla", profissao="Noiva", texto="Penteado maravilhoso"),
    ]


def test_filtrar_depoimentos_por_profissao(api, varios):
    """[Recursos adicionais] Filtrar depoimentos por profissão
    Esperado: somente os de 'noiva' (2), sem diferenciar maiúsculas."""
    assert api.get("/api/depoimentos?profissao=noiva").json()["count"] == 2


def test_buscar_depoimentos(api, varios):
    """[Recursos adicionais] Buscar depoimentos por texto (search)
    Esperado: 'penteado' encontra 1 resultado."""
    r = api.get("/api/depoimentos?search=penteado").json()
    assert r["count"] == 1 and r["results"][0]["nome_autor"] == "Carla"


def test_ordenar_depoimentos(api, varios):
    """[Recursos adicionais] Ordenar depoimentos por nome
    Esperado: 'nome_autor' em ordem crescente e '-nome_autor' em decrescente."""
    asc = [d["nome_autor"] for d in api.get("/api/depoimentos?ordering=nome_autor").json()["results"]]
    desc = [d["nome_autor"] for d in api.get("/api/depoimentos?ordering=-nome_autor").json()["results"]]
    assert asc == ["Ana", "Bia", "Carla"] and desc == ["Carla", "Bia", "Ana"]


def test_paginar_depoimentos(api, varios):
    """[Recursos adicionais] Paginar depoimentos com page_size=2
    Esperado: 2 itens na página 1, 1 item na página 2 e count=3."""
    assert len(api.get("/api/depoimentos?page_size=2").json()["results"]) == 2
    p2 = api.get("/api/depoimentos?page_size=2&page=2").json()
    assert p2["count"] == 3 and len(p2["results"]) == 1


def test_page_size_maximo(api, varios):
    """[Recursos adicionais] page_size acima do máximo (100)
    Esperado: a API limita o tamanho da página a 100 (HTTP 200)."""
    r = api.get("/api/depoimentos?page_size=100000")
    assert r.status_code == 200 and r.json()["count"] == 3
