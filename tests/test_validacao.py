"""Validação de dados de entrada e tratamento de erros (400, 404, 405, 415)."""
import pytest

from .helpers import SENHA, verificar_erro

pytestmark = pytest.mark.django_db

CADASTRO = {
    "nome": "Maria Souza",
    "email": "maria@email.com",
    "telefone": "61999999999",
    "senha": SENHA,
}


def cadastrar(api, **alteracoes):
    return api.post("/api/auth/cadastro", {**CADASTRO, **alteracoes}, format="json")


# ------------------------------------------------------- campos obrigatórios
def test_cadastro_campos_obrigatorios_ausentes(api):
    """[Validação] Cadastro sem nenhum campo obrigatório
    Esperado: HTTP 400 com um erro para cada campo (nome, email, telefone, senha)."""
    corpo = verificar_erro(api.post("/api/auth/cadastro", {}, format="json"), 400)
    assert set(corpo["detalhes"]) == {"nome", "email", "telefone", "senha"}


def test_mensagem_campos_obrigatorios_ausentes(api_usuario):
    """[Validação] Mensagem sem serviço e sem texto
    Esperado: HTTP 400 com erros em servico e mensagem."""
    corpo = verificar_erro(api_usuario.post("/api/mensagens", {}, format="json"), 400)
    assert set(corpo["detalhes"]) == {"servico", "mensagem"}


def test_depoimento_campos_obrigatorios_ausentes(api_admin):
    """[Validação] Depoimento sem campos obrigatórios
    Esperado: HTTP 400 com erros em nome_autor, profissao e texto."""
    corpo = verificar_erro(api_admin.post("/api/depoimentos", {}, format="json"), 400)
    assert set(corpo["detalhes"]) == {"nome_autor", "profissao", "texto"}


def test_campo_em_branco(api_usuario):
    """[Validação] Mensagem só com espaços em branco
    Esperado: HTTP 400 (texto vazio não é aceito)."""
    r = api_usuario.post("/api/mensagens", {"servico": "NOIVAS", "mensagem": "     "}, format="json")
    assert "mensagem" in verificar_erro(r, 400)["detalhes"]


# --------------------------------------------------------- tipos incorretos
@pytest.mark.parametrize(
    "campo,valor",
    [("nome", 12345), ("telefone", 61999999999), ("senha", ["a", "b"]), ("email", {"x": 1})],
)
def test_cadastro_tipos_incorretos(api, campo, valor):
    """[Validação] Cadastro com tipo de dado incorreto (número, lista ou objeto em campo de texto)
    Esperado: HTTP 400 com erro no campo enviado."""
    corpo = verificar_erro(cadastrar(api, **{campo: valor}), 400)
    assert campo in corpo["detalhes"]


@pytest.mark.parametrize("valor", [123, True, ["NOIVAS"], None])
def test_mensagem_tipos_incorretos(api_usuario, valor):
    """[Validação] Mensagem com tipo incorreto no texto (número, booleano, lista ou nulo)
    Esperado: HTTP 400 com erro no campo mensagem."""
    r = api_usuario.post("/api/mensagens", {"servico": "NOIVAS", "mensagem": valor}, format="json")
    assert "mensagem" in verificar_erro(r, 400)["detalhes"]


# --------------------------------------------------------- regras de formato
@pytest.mark.parametrize("email", ["sem-arroba", "a@", "@b.com", "a b@c.com", ""])
def test_cadastro_email_invalido(api, email):
    """[Validação] Cadastro com e-mail em formato inválido
    Esperado: HTTP 400 com erro em email."""
    assert "email" in verificar_erro(cadastrar(api, email=email), 400)["detalhes"]


@pytest.mark.parametrize("telefone", ["abc", "123", "(61) 9999", "6199999999999999", "61-99999-99x9"])
def test_cadastro_telefone_invalido(api, telefone):
    """[Validação] Cadastro com telefone inválido
    Esperado: HTTP 400 com erro em telefone."""
    assert "telefone" in verificar_erro(cadastrar(api, telefone=telefone), 400)["detalhes"]


@pytest.mark.parametrize("telefone", ["61999999999", "(61) 99999-9999", "+55 61 99999-9999", "6133334444"])
def test_cadastro_telefone_aceita_formatos_comuns(api, telefone):
    """[Validação] Telefones brasileiros em formatos comuns
    Esperado: HTTP 201."""
    assert cadastrar(api, telefone=telefone).status_code == 201


@pytest.mark.parametrize("senha", ["curta1!", "12345678", "password", "11111111"])
def test_cadastro_senha_fraca(api, senha):
    """[Validação] Senha curta, só numérica ou muito comum
    Esperado: HTTP 400 com explicação da regra violada."""
    corpo = verificar_erro(cadastrar(api, senha=senha), 400)
    assert "senha" in corpo["detalhes"] or "non_field_errors" in corpo["detalhes"]


def test_cadastro_nome_muito_longo(api):
    """[Validação] Nome com mais de 120 caracteres
    Esperado: HTTP 400 com erro em nome."""
    assert "nome" in verificar_erro(cadastrar(api, nome="A" * 121), 400)["detalhes"]


def test_mensagem_servico_invalido(api_usuario):
    """[Validação] Serviço fora da enumeração (NOIVAS, AUDIOVISUAL, CORTE_CABELO, CARACTERIZACAO, OUTROS)
    Esperado: HTTP 400 listando os valores aceitos."""
    r = api_usuario.post("/api/mensagens", {"servico": "MASSAGEM", "mensagem": "Oi"}, format="json")
    corpo = verificar_erro(r, 400)
    assert "NOIVAS" in corpo["detalhes"]["servico"][0]


def test_mensagem_acima_do_limite(api_usuario):
    """[Validação] Mensagem com mais de 1000 caracteres
    Esperado: HTTP 400 com erro em mensagem."""
    r = api_usuario.post("/api/mensagens", {"servico": "OUTROS", "mensagem": "x" * 1001}, format="json")
    assert "mensagem" in verificar_erro(r, 400)["detalhes"]


def test_mensagem_no_limite_e_aceita(api_usuario):
    """[Validação] Mensagem com exatamente 1000 caracteres
    Esperado: HTTP 201."""
    r = api_usuario.post("/api/mensagens", {"servico": "OUTROS", "mensagem": "x" * 1000}, format="json")
    assert r.status_code == 201


def test_depoimento_texto_acima_do_limite(api_admin):
    """[Validação] Depoimento com mais de 2000 caracteres
    Esperado: HTTP 400 com erro em texto."""
    dados = {"nome_autor": "Ana", "profissao": "Noiva", "texto": "x" * 2001}
    assert "texto" in verificar_erro(api_admin.post("/api/depoimentos", dados, format="json"), 400)["detalhes"]


def test_atualizacao_de_perfil_telefone_invalido(api_usuario):
    """[Validação] Atualizar o próprio cadastro com telefone inválido
    Esperado: HTTP 400 com erro em telefone."""
    r = api_usuario.patch("/api/usuarios/me", {"telefone": "abc"}, format="json")
    assert "telefone" in verificar_erro(r, 400)["detalhes"]


def test_put_exige_todos_os_campos(api_usuario):
    """[Validação] PUT (atualização completa) sem enviar todos os campos
    Esperado: HTTP 400 apontando o campo ausente."""
    r = api_usuario.put("/api/usuarios/me", {"nome": "Só o nome"}, format="json")
    assert "telefone" in verificar_erro(r, 400)["detalhes"]


# ------------------------------------------------- requisições malformadas
def test_json_malformado(api):
    """[Validação] Corpo da requisição com JSON malformado
    Esperado: HTTP 400 com mensagem clara."""
    r = api.post("/api/auth/login", data="{email: sem aspas", content_type="application/json")
    assert "JSON" in verificar_erro(r, 400)["mensagem"]


def test_corpo_que_nao_e_objeto(api):
    """[Validação] Corpo JSON que é uma lista em vez de objeto
    Esperado: HTTP 400."""
    verificar_erro(api.post("/api/auth/login", [1, 2, 3], format="json"), 400)


def test_content_type_nao_suportado(api):
    """[Validação] Envio como formulário (não JSON)
    Esperado: HTTP 415."""
    r = api.post("/api/auth/login", data="email=a@b.com&senha=x", content_type="application/x-www-form-urlencoded")
    verificar_erro(r, 415)


# --------------------------------------------------- registros inexistentes
def test_mensagem_inexistente(api_usuario):
    """[Validação] Consultar registro que não existe
    Esperado: HTTP 404 no formato padrão de erro."""
    verificar_erro(api_usuario.get("/api/mensagens/99999"), 404)


def test_id_nao_numerico(api_usuario):
    """[Validação] Identificador que não é número
    Esperado: HTTP 404 (e não erro 500)."""
    verificar_erro(api_usuario.get("/api/mensagens/abc"), 404)


def test_depoimento_inexistente(api):
    """[Validação] Consultar depoimento inexistente
    Esperado: HTTP 404."""
    verificar_erro(api.get("/api/depoimentos/99999"), 404)


def test_atualizar_e_excluir_inexistentes(api_admin):
    """[Validação] Atualizar e excluir registro que não existe
    Esperado: HTTP 404 em ambos."""
    verificar_erro(api_admin.patch("/api/depoimentos/99999", {"texto": "x"}, format="json"), 404)
    verificar_erro(api_admin.delete("/api/depoimentos/99999"), 404)


def test_rota_inexistente(api):
    """[Validação] Endereço que não existe
    Esperado: HTTP 404 em JSON."""
    r = api.get("/api/nao-existe")
    verificar_erro(r, 404)


def test_metodo_nao_permitido(api):
    """[Validação] Método HTTP não suportado pelo endpoint
    Esperado: HTTP 405."""
    verificar_erro(api.delete("/api/auth/login"), 405)


# ---------------------------------------------------- parâmetros de consulta
def test_filtro_de_data_invalido(api):
    """[Validação] Filtro de data em formato inválido
    Esperado: HTTP 400 com erro em data_inicio."""
    corpo = verificar_erro(api.get("/api/depoimentos?data_inicio=ontem"), 400)
    assert "data_inicio" in corpo["detalhes"]


def test_pagina_inexistente(api):
    """[Validação] Página fora do intervalo
    Esperado: HTTP 404."""
    verificar_erro(api.get("/api/depoimentos?page=50"), 404)
