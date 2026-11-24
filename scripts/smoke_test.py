#!/usr/bin/env python
"""
Teste de fumaça (smoke test) da API em QUALQUER endereço, inclusive a URL pública.

Percorre os principais cenários da rubrica (hospedagem, autenticação, CRUD,
validação, autorização e recursos adicionais) e gera uma tabela com o
resultado ESPERADO x OBTIDO, pronta para colar no relatório de testes.

Uso:
    pip install requests
    python scripts/smoke_test.py https://SUA-API.onrender.com
    python scripts/smoke_test.py https://SUA-API.onrender.com \
        --admin-email camila@email.com --admin-senha 'SENHA_DO_ADMIN'
    python scripts/smoke_test.py http://127.0.0.1:8000        # servidor local

Opções:
    --saida ARQUIVO.md   grava a tabela em Markdown (padrão: docs/evidencias/...)
    --timeout 90         segundos de espera por resposta (a 1ª requisição em
                         hospedagem gratuita pode demorar para "acordar")

O script cria um usuário descartável (smoke+...@example.com) e o exclui no fim.
Sai com código 1 se algum cenário falhar.
"""
import argparse
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests

SENHA = "Smoke@Teste2026"


class Executor:
    def __init__(self, base, timeout):
        self.base = base.rstrip("/")
        self.timeout = timeout
        self.sessao = requests.Session()
        self.linhas = []

    def req(self, categoria, descricao, metodo, caminho, esperado, token=None, **kw):
        """Faz a requisição, registra esperado x obtido e devolve a resposta."""
        cab = kw.pop("headers", {})
        if token:
            cab["Authorization"] = f"Bearer {token}"
        url = caminho if caminho.startswith("http") else self.base + caminho
        inicio = time.perf_counter()
        try:
            r = self.sessao.request(metodo, url, headers=cab, timeout=self.timeout, allow_redirects=False, **kw)
            obtido, ms = r.status_code, int((time.perf_counter() - inicio) * 1000)
        except requests.RequestException as erro:
            r, obtido, ms = None, f"erro: {type(erro).__name__}", 0
        ok = obtido == esperado
        n = len(self.linhas) + 1
        self.linhas.append((f"HT-{n:02d}", categoria, descricao, f"{metodo} {caminho.replace(self.base, '')}", esperado, obtido, ms, ok))
        print(f"{'OK ' if ok else 'ERRO'} HT-{n:02d} [{categoria}] {descricao}: esperado {esperado}, obtido {obtido} ({ms} ms)")
        return r


def json_ou_vazio(r):
    try:
        return r.json()
    except Exception:
        return {}


def executar(ex, admin_email, admin_senha):
    base = ex.base
    https = base.startswith("https://")
    unico = datetime.now().strftime("%Y%m%d%H%M%S")
    email = f"smoke+{unico}@example.com"
    cadastro = {"nome": "Usuária de Teste", "email": email, "telefone": "61999999999", "senha": SENHA}

    # --- Hospedagem
    ex.req("Hospedagem", "Health check da API", "GET", "/api/saude", 200)
    ex.req("Hospedagem", "Swagger UI disponível", "GET", "/api/docs", 200)
    ex.req("Hospedagem", "Esquema OpenAPI disponível", "GET", "/api/schema", 200, headers={"Accept": "application/json"})
    ex.req("Hospedagem", "ReDoc disponível", "GET", "/api/redoc", 200)
    if https:
        http_url = "http://" + base[len("https://"):] + "/api/depoimentos"
        ex.req("Hospedagem", "HTTP redireciona para HTTPS", "GET", http_url, 301)

    # --- Autenticação
    ex.req("Autenticação", "Rota protegida sem token", "GET", "/api/usuarios/me", 401)
    ex.req("Autenticação", "Cadastro de usuário válido", "POST", "/api/auth/cadastro", 201, json=cadastro)
    ex.req("Validação", "Cadastro com e-mail já existente", "POST", "/api/auth/cadastro", 409, json=cadastro)
    ex.req("Autenticação", "Login com senha incorreta", "POST", "/api/auth/login", 401, json={"email": email, "senha": "Errada#12345"})
    r = ex.req("Autenticação", "Login com credenciais válidas", "POST", "/api/auth/login", 200, json={"email": email, "senha": SENHA})
    token = json_ou_vazio(r).get("access") if r is not None else None
    ex.req("Autenticação", "Rota protegida com token válido", "GET", "/api/usuarios/me", 200, token=token)
    ex.req("Autenticação", "Rota protegida com token inválido", "GET", "/api/usuarios/me", 401, token="token.invalido.xyz")

    # --- Validação
    ex.req("Validação", "Cadastro sem campos obrigatórios", "POST", "/api/auth/cadastro", 400, json={})
    ex.req("Validação", "Cadastro com e-mail inválido", "POST", "/api/auth/cadastro", 400, json={**cadastro, "email": "sem-arroba"})
    ex.req("Validação", "Cadastro com tipo incorreto (nome numérico)", "POST", "/api/auth/cadastro", 400, json={**cadastro, "nome": 123})
    ex.req("Validação", "Mensagem com serviço inválido", "POST", "/api/mensagens", 400, token=token, json={"servico": "XYZ", "mensagem": "Oi"})
    ex.req("Validação", "Mensagem sem texto", "POST", "/api/mensagens", 400, token=token, json={"servico": "NOIVAS"})
    ex.req("Validação", "Registro inexistente", "GET", "/api/mensagens/99999999", 404, token=token)

    # --- CRUD de mensagens
    r = ex.req("CRUD", "Criar mensagem", "POST", "/api/mensagens", 201, token=token,
               json={"servico": "NOIVAS", "mensagem": "Teste automatizado de contato."})
    mid = json_ou_vazio(r).get("id") if r is not None else None
    ex.req("CRUD", "Listar mensagens", "GET", "/api/mensagens", 200, token=token)
    ex.req("CRUD", "Consultar mensagem", "GET", f"/api/mensagens/{mid}", 200, token=token)
    ex.req("CRUD", "Atualizar mensagem (PUT)", "PUT", f"/api/mensagens/{mid}", 200, token=token,
           json={"servico": "AUDIOVISUAL", "mensagem": "Texto atualizado."})
    ex.req("CRUD", "Atualizar mensagem (PATCH)", "PATCH", f"/api/mensagens/{mid}", 200, token=token, json={"servico": "OUTROS"})
    ex.req("Recursos adicionais", "Filtrar mensagens por serviço", "GET", "/api/mensagens?servico=OUTROS", 200, token=token)
    ex.req("Recursos adicionais", "Buscar e ordenar mensagens", "GET", "/api/mensagens?search=atualizado&ordering=-enviado_em", 200, token=token)
    ex.req("CRUD", "Excluir mensagem", "DELETE", f"/api/mensagens/{mid}", 204, token=token)
    ex.req("CRUD", "Consultar mensagem excluída", "GET", f"/api/mensagens/{mid}", 404, token=token)

    # --- Autorização
    ex.req("Autorização", "Usuário comum acessa rota de ADMIN", "GET", "/api/admin/usuarios", 403, token=token)
    ex.req("Autorização", "Usuário comum cria depoimento", "POST", "/api/depoimentos", 403, token=token,
           json={"nome_autor": "X", "profissao": "Y", "texto": "Z"})

    # --- Depoimentos públicos e recursos adicionais
    ex.req("CRUD", "Listar depoimentos (público)", "GET", "/api/depoimentos", 200)
    ex.req("Recursos adicionais", "Paginação de depoimentos", "GET", "/api/depoimentos?page=1&page_size=2", 200)
    ex.req("Recursos adicionais", "Busca e ordenação de depoimentos", "GET", "/api/depoimentos?search=noiva&ordering=-criado_em", 200)

    # --- ADMIN (opcional)
    if admin_email and admin_senha:
        r = ex.req("Autenticação", "Login do ADMIN", "POST", "/api/auth/login", 200, json={"email": admin_email, "senha": admin_senha})
        adm = json_ou_vazio(r).get("access") if r is not None else None
        r = ex.req("CRUD", "ADMIN cria depoimento", "POST", "/api/depoimentos", 201, token=adm,
                   json={"nome_autor": "Cliente Teste", "profissao": "Noiva", "texto": "Depoimento de teste automatizado."})
        did = json_ou_vazio(r).get("id") if r is not None else None
        ex.req("CRUD", "Consultar depoimento (público)", "GET", f"/api/depoimentos/{did}", 200)
        ex.req("CRUD", "ADMIN atualiza depoimento", "PATCH", f"/api/depoimentos/{did}", 200, token=adm, json={"profissao": "Atriz"})
        ex.req("CRUD", "ADMIN exclui depoimento", "DELETE", f"/api/depoimentos/{did}", 204, token=adm)
        ex.req("Autorização", "ADMIN lista usuários", "GET", "/api/admin/usuarios?page_size=5", 200, token=adm)
        ex.req("Autorização", "ADMIN consulta histórico de logins", "GET", "/api/admin/logins?status=SUCESSO", 200, token=adm)
        ex.req("Autorização", "ADMIN consulta indicadores de acesso", "GET", "/api/admin/logins/resumo", 200, token=adm)

    # --- Limpeza: exclui a conta descartável (também testa o DELETE de usuário)
    ex.req("CRUD", "Excluir a própria conta (limpeza)", "DELETE", "/api/usuarios/me", 204, token=token)


def tabela_markdown(ex, base):
    ok = sum(1 for linha in ex.linhas if linha[-1])
    total = len(ex.linhas)
    saida = [
        f"# Resultado do teste de fumaça",
        "",
        f"- **URL testada:** {base}",
        f"- **Data/hora:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
        f"- **Resultado:** {ok} de {total} cenários conforme o esperado",
        "",
        "| ID | Categoria | Cenário | Requisição | Esperado | Obtido | Tempo | Status |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for id_, cat, desc, req, esp, obt, ms, passou in ex.linhas:
        saida.append(f"| {id_} | {cat} | {desc} | `{req}` | HTTP {esp} | HTTP {obt} | {ms} ms | {'✅ Aprovado' if passou else '❌ Falhou'} |")
    return "\n".join(saida) + "\n"


def main():
    p = argparse.ArgumentParser(description="Smoke test da Camila Lee API")
    p.add_argument("url", help="URL base da API, ex.: https://minha-api.onrender.com")
    p.add_argument("--admin-email")
    p.add_argument("--admin-senha")
    p.add_argument("--saida")
    p.add_argument("--timeout", type=int, default=90)
    a = p.parse_args()

    ex = Executor(a.url, a.timeout)
    executar(ex, a.admin_email, a.admin_senha)

    md = tabela_markdown(ex, ex.base)
    host = urlparse(ex.base).netloc.replace(":", "_")
    destino = Path(a.saida) if a.saida else Path("docs/evidencias") / f"smoke_{host}_{datetime.now():%Y%m%d_%H%M%S}.md"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(md, encoding="utf-8")
    ok = all(linha[-1] for linha in ex.linhas)
    print(f"\n{'TODOS OS CENÁRIOS PASSARAM' if ok else 'HÁ CENÁRIOS COM FALHA'} — relatório: {destino}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
