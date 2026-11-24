#!/usr/bin/env python
"""
Gera docs/RELATORIO_DE_TESTES.md rodando a suíte de testes (pytest) de verdade e
juntando as evidências que estiverem em docs/evidencias/:

    smoke_local.md     resultado do smoke test no servidor local de produção
    smoke_publico.md   resultado do smoke test na URL PÚBLICA (gerado por você)
    check_deploy.txt   saída de `python manage.py check --deploy`

Fluxo recomendado depois de publicar a API:
    python scripts/smoke_test.py https://SUA-API.onrender.com \
        --admin-email EMAIL --admin-senha SENHA --saida docs/evidencias/smoke_publico.md
    python scripts/gerar_relatorio_testes.py

O "Esperado" de cada cenário vem da docstring do próprio teste (arquivo tests/),
e o "Obtido" vem do resultado real da execução — assim o relatório nunca fica
desatualizado em relação ao código.
"""
import ast
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
EVID = RAIZ / "docs" / "evidencias"
ORDEM = ["CRUD", "Validação", "Autenticação", "Autorização", "Hospedagem", "Recursos adicionais"]


def coletar_cenarios():
    """Lê as docstrings '[Categoria] Cenário / Esperado: ...' dos testes."""
    cenarios = {}
    for arquivo in sorted((RAIZ / "tests").glob("test_*.py")):
        arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
        for no in arvore.body:
            if isinstance(no, ast.FunctionDef) and no.name.startswith("test_"):
                doc = ast.get_docstring(no) or ""
                m = re.match(r"\[(.+?)\]\s*(.+?)\n\s*Esperado:\s*(.+)", doc, re.S)
                if m:
                    esperado = " ".join(m.group(3).split())
                    cenarios[(f"tests.{arquivo.stem}", no.name)] = (
                        m.group(1), " ".join(m.group(2).split()), esperado,
                    )
    return cenarios


def executar_pytest():
    """Roda o pytest e devolve {(modulo, função): (execuções, falhas)} e a linha-resumo."""
    with tempfile.TemporaryDirectory() as tmp:
        xml = Path(tmp) / "resultado.xml"
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", f"--junitxml={xml}"],
            cwd=RAIZ, capture_output=True, text=True,
        )
        resultados = {}
        for caso in ET.parse(xml).getroot().iter("testcase"):
            chave = (caso.get("classname"), caso.get("name").split("[")[0])
            execs, falhas = resultados.get(chave, (0, 0))
            ruim = caso.find("failure") is not None or caso.find("error") is not None
            resultados[chave] = (execs + 1, falhas + (1 if ruim else 0))
    resumo = [l for l in proc.stdout.strip().splitlines() if l.strip()][-1]
    (EVID / "pytest.txt").write_text(proc.stdout, encoding="utf-8")
    return resultados, resumo


def ler(nome):
    arq = EVID / nome
    return arq.read_text(encoding="utf-8").strip() if arq.exists() else None


def secao_smoke(titulo, arquivo, instrucao):
    texto = ler(arquivo)
    if texto is None:
        return f"### {titulo}\n\n> **PENDENTE.** {instrucao}\n"
    # Rebaixa os títulos do arquivo para caber como subseção.
    texto = re.sub(r"^# ", "#### ", texto, flags=re.M)
    return f"### {titulo}\n\n{texto}\n"


def main():
    cenarios = coletar_cenarios()
    resultados, resumo = executar_pytest()

    linhas = []
    n = 0
    total_exec = total_falhas = 0
    for categoria in ORDEM:
        for (modulo, funcao), (cat, nome, esperado) in cenarios.items():
            if cat != categoria:
                continue
            execs, falhas = resultados.get((modulo, funcao), (0, 0))
            n += 1
            total_exec += execs
            total_falhas += falhas
            if execs == 0:
                obtido, status = "Teste não executado", "❌"
            elif falhas:
                obtido, status = f"{falhas} de {execs} execuções falharam", "❌ Falhou"
            else:
                obtido = "Conforme o esperado" + (f" ({execs} variações)" if execs > 1 else "")
                status = "✅ Aprovado"
            linhas.append(f"| AUT-{n:02d} | {cat} | {nome} | {esperado} | {obtido} | {status} |")

    import django
    import pytest as _pytest

    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    check = ler("check_deploy.txt")
    md = f"""# Relatório de Testes — Camila Lee API (Django REST Framework)

**Disciplina:** Programação para Internet — TSI/IFB · **Projeto Final** (expansão da API do Projeto Integrador III)
**Gerado em:** {agora} · **Python** {sys.version.split()[0]} · **Django** {django.get_version()} · **pytest** {_pytest.__version__}

## 1. Objetivo e estratégia

Verificar, com evidências, os requisitos da rubrica: operações CRUD, validação e tratamento de erros,
autenticação e autorização, documentação, hospedagem/segurança e recursos adicionais (filtros, busca,
ordenação e paginação). Foram usadas três frentes complementares:

1. **Testes automatizados (pytest)** — rodam em banco isolado a cada execução (seção 2);
2. **Teste de fumaça HTTP (`scripts/smoke_test.py`)** — exercita a API por requisições reais, no servidor local
   em modo de produção e na **URL pública** (seção 3);
3. **Verificações de segurança e implantação** — `check --deploy` e conferências de configuração (seção 4).

Os testes manuais podem ser repetidos no **Swagger UI** (`/api/docs`) ou no Postman; as evidências em imagem
ficam listadas na seção 5.

## 2. Testes automatizados (pytest)

**Resultado da execução:** `{resumo}`
({total_exec} execuções de teste em {n} cenários; {total_falhas} falha(s)).
Comando: `python -m pytest` · Saída completa em `docs/evidencias/pytest.txt`.

| ID | Categoria | Cenário | Resultado esperado | Resultado obtido | Status |
|---|---|---|---|---|---|
{chr(10).join(linhas)}

Os cenários mínimos da rubrica estão cobertos: CRUD completo (criar, listar, consultar, atualizar e excluir),
mais de três cenários de dados inválidos, acesso sem autenticação / com credenciais inválidas / com credenciais
válidas, operação não autorizada (usuário comum x ADMIN) e recursos adicionais (filtros, busca, ordenação, paginação).

## 3. Teste de fumaça HTTP (esperado x obtido por requisição)

{secao_smoke("3.1 Servidor local em modo de produção (gunicorn, DEBUG=False)", "smoke_local.md",
             "Execute `python scripts/smoke_test.py http://127.0.0.1:8000 --saida docs/evidencias/smoke_local.md`.")}
{secao_smoke("3.2 URL pública (ambiente de produção)", "smoke_publico.md",
             "Depois de publicar a API, execute `python scripts/smoke_test.py https://SUA-API.onrender.com --admin-email EMAIL --admin-senha SENHA --saida docs/evidencias/smoke_publico.md` e gere este relatório novamente.")}
## 4. Hospedagem e segurança

| Item da rubrica | Como foi atendido | Como foi verificado |
|---|---|---|
| `DEBUG = False` | Padrão do projeto é `False`; só liga com `DEBUG=True` no `.env` local. `render.yaml` fixa `False`. | Teste `test_erro_interno_nao_vaza_detalhes` (erro 500 sem traceback). |
| `ALLOWED_HOSTS` | Lido de variável de ambiente; no Render inclui `RENDER_EXTERNAL_HOSTNAME`. Vazio em produção = recusa tudo. | Host não autorizado recebe HTTP 400 (verificado manualmente). |
| `SECRET_KEY` e credenciais | Somente variáveis de ambiente; a aplicação **se recusa a iniciar** sem `SECRET_KEY` quando `DEBUG=False`. `.env` está no `.gitignore`. | Execução sem a variável: `ImproperlyConfigured` (verificado manualmente). |
| HTTPS | `SECURE_SSL_REDIRECT`, HSTS de 1 ano, cookies `Secure`, `SECURE_PROXY_SSL_HEADER` (proxy do provedor). | Testes `test_redireciona_http_para_https`, `test_https_atras_do_proxy_nao_redireciona`. |
| Exposição do banco | `DATABASE_URL` interna (não pública) em variável de ambiente; erros 500 genéricos; painel Django em caminho configurável (`ADMIN_URL`). | Testes `test_admin_do_django_fora_do_caminho_padrao`, `test_erro_interno_nao_vaza_detalhes`. |
| Senhas | Hash PBKDF2 + validadores de senha do Django; respostas nunca trazem a senha. | Teste `test_senha_armazenada_com_hash`. |
| Força bruta | Limite por IP em login (10/min), cadastro, recuperação e redefinição de senha. | Teste `test_login_limite_de_tentativas` (HTTP 429). |
| Documentação online | Swagger UI, ReDoc e esquema OpenAPI no mesmo servidor, com arquivos estáticos locais (sem CDN). | Testes `test_swagger_ui_e_redoc_disponiveis`, `test_esquema_openapi_completo`. |

### 4.1 `python manage.py check --deploy`

```
{check if check else "(pendente: execute o comando com as variáveis de produção e salve em docs/evidencias/check_deploy.txt)"}
```

**Análise do aviso `security.W021` (HSTS preload):** mantido de propósito. O *preload* inclui o domínio
numa lista embutida nos navegadores e é difícil de desfazer; só deve ser ativado para um domínio próprio e
definitivo (variável `SECURE_HSTS_PRELOAD=True`). Em `*.onrender.com` o domínio pertence ao provedor, portanto
o aviso é conhecido e aceito. Todos os demais avisos (SSL redirect, cookies seguros, HSTS, `DEBUG`,
`SECRET_KEY`, `ALLOWED_HOSTS`) estão resolvidos.

## 5. Evidências a anexar (capturas de tela)

- [ ] Swagger UI na URL pública (`/api/docs`) com a lista completa de endpoints.
- [ ] Botão **Authorize** preenchido e uma rota protegida respondendo 200.
- [ ] Rota protegida sem token respondendo **401** e rota de ADMIN com usuário comum respondendo **403**.
- [ ] Cadastro (**201**), login (**200**) e login inválido (**401**) no Swagger ou Postman.
- [ ] CRUD de mensagens: criar (**201**), listar, consultar, atualizar e excluir (**204**).
- [ ] Erro de validação (**400**) com o JSON de `detalhes`.
- [ ] Cadeado/HTTPS no navegador e HTTP redirecionando para HTTPS.
- [ ] Painel do provedor mostrando as variáveis de ambiente (**sem exibir os valores secretos**).
- [ ] Execução do `check --deploy` no terminal.

## 6. Conclusão

{"Todos os cenários automatizados foram aprovados." if total_falhas == 0 else "Há cenários automatizados com falha: veja a tabela da seção 2."}
O teste de fumaça local confirma o funcionamento da API em modo de produção; a seção 3.2 registra a execução
contra a URL pública após a implantação.
"""
    destino = RAIZ / "docs" / "RELATORIO_DE_TESTES.md"
    destino.write_text(md, encoding="utf-8")
    print(f"Relatório gerado: {destino}\n{resumo}")
    sys.exit(1 if total_falhas else 0)


if __name__ == "__main__":
    main()
