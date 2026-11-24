# Publicação da API (hospedagem, HTTPS e segurança)

Este guia publica a API no **Render** (plano gratuito) usando o `render.yaml` e o `build.sh` do repositório. O mesmo código roda em qualquer hospedagem Python que aceite um servidor WSGI (PythonAnywhere, Railway, Fly.io...): o que muda é só onde se preenchem as variáveis de ambiente.

## 1. Antes de começar

1. O código precisa estar num repositório **GitHub** (o Render lê de lá). Confira que o `.env` e o `db.sqlite3` **não** foram enviados (o `.gitignore` já os ignora).
2. Rode `python -m pytest` localmente: todos os testes devem passar.
3. Tenha em mãos: o e-mail e uma senha forte para o ADMIN inicial.

## 2. Publicar com Blueprint (recomendado)

1. Em <https://dashboard.render.com> → **New → Blueprint** → conecte o repositório. O Render lê o `render.yaml` e propõe criar:
   - um banco **PostgreSQL** `camilalee-db`;
   - um serviço web **camilalee-api**.
2. Ele pedirá os valores das variáveis marcadas como `sync: false` (não ficam no GitHub):
   - `ADMIN_EMAIL` e `ADMIN_SENHA` — cria o usuário ADMIN no primeiro deploy;
   - `CORS_ALLOWED_ORIGINS` — endereço do front-end, se houver (pode deixar vazio por enquanto).
3. Clique em **Apply**. O build roda `build.sh`: instala dependências, `collectstatic`, `migrate` (cria as tabelas e os perfis ADMIN/USUARIO) e `criar_admin`.
4. Quando o deploy ficar **Live**, abra `https://SEU-SERVICO.onrender.com/api/docs`. O Render fornece HTTPS automaticamente.

O `render.yaml` já configura: `DEBUG=False`, `SECRET_KEY` gerada pelo Render, `DATABASE_URL` com a **URL interna** do banco, `NUM_PROXIES=1` e o health check `/api/saude`. O domínio entra em `ALLOWED_HOSTS` sozinho (variável `RENDER_EXTERNAL_HOSTNAME`).

### Publicar manualmente (sem Blueprint)

| Campo | Valor |
|---|---|
| Language | Python 3 |
| Build Command | `bash build.sh` |
| Start Command | `python -m gunicorn config.wsgi:application` |
| Health Check Path | `/api/saude` |
| Variáveis | `DEBUG=False`, `SECRET_KEY` (gere uma), `DATABASE_URL` (URL **interna** do PostgreSQL), `NUM_PROXIES=1`, `ADMIN_EMAIL`, `ADMIN_SENHA` |

Gere uma `SECRET_KEY` com: `python -c "import secrets; print(secrets.token_urlsafe(60))"`.

## 3. Conferir se está tudo certo

```bash
# 1) Teste de fumaça na URL pública (inclui os cenários de ADMIN)
python scripts/smoke_test.py https://SEU-SERVICO.onrender.com \
    --admin-email SEU_EMAIL_ADMIN --admin-senha 'SUA_SENHA' \
    --saida docs/evidencias/smoke_publico.md

# 2) Regenerar o relatório de testes com essa evidência
python scripts/gerar_relatorio_testes.py
```

Também confira manualmente: o cadeado de HTTPS no navegador; `http://SEU-SERVICO.onrender.com/api/depoimentos` redirecionando para `https://`; e o Swagger UI funcionando com **Authorize**.

### `check --deploy`

Rode com as mesmas variáveis do ambiente de produção (`SECRET_KEY` forte, `DEBUG=False`) e guarde a saída em `docs/evidencias/check_deploy.txt`:

```bash
DEBUG=False SECRET_KEY="<chave forte>" ALLOWED_HOSTS=SEU-SERVICO.onrender.com python manage.py check --deploy
```

O resultado esperado é **um único aviso**, `security.W021` (HSTS *preload*), que é intencional: o preload só vale para um domínio próprio e definitivo, e `onrender.com` pertence ao provedor. Se um dia usar domínio próprio, defina `SECURE_HSTS_PRELOAD=True`.

## 4. Limites do plano gratuito do Render (conferidos em 24/11/2026)

Fonte: documentação oficial do Render sobre [instâncias gratuitas](https://render.com/docs/free). Os limites podem mudar; confirme no site.

- O serviço **hiberna após 15 minutos** sem requisições e leva cerca de **1 minuto** para acordar. **Antes da apresentação, abra `/api/saude` uns 2 minutos antes** para “acordar” a API. O `smoke_test.py` espera até 90 s por resposta justamente por isso.
- O PostgreSQL gratuito **expira 30 dias após a criação** (com 14 dias de carência antes de ser apagado). Crie o banco perto da entrega e **não conte com ele depois da avaliação**.
- Não há acesso a terminal (shell) no plano gratuito — por isso o ADMIN é criado pelo `criar_admin` no build.
- O sistema de arquivos é efêmero (a API não grava arquivos; todo dado vai para o PostgreSQL).
- **Saída pelas portas SMTP 25, 465 e 587 é bloqueada.** Com `EMAIL_HOST` configurado nessas portas, o e-mail com o código de recuperação de senha **não será entregue** (a API continua respondendo 200 e registra o erro no log). Para demonstrar a recuperação de senha em produção, use um provedor de e-mail que aceite outra porta ou uma API HTTPS, ou demonstre esse fluxo localmente (onde o código aparece no terminal).

## 5. Segurança — o que está configurado e onde

| Requisito | Configuração |
|---|---|
| `DEBUG = False` | `DEBUG` lida do ambiente; padrão `False`; `render.yaml` fixa `False` |
| `ALLOWED_HOSTS` | `ALLOWED_HOSTS` + `RENDER_EXTERNAL_HOSTNAME`; vazio em produção recusa qualquer host |
| `SECRET_KEY`, senhas, tokens | Só em variáveis de ambiente; o app não inicia sem `SECRET_KEY` quando `DEBUG=False`; `.env` no `.gitignore` |
| HTTPS | `SECURE_SSL_REDIRECT`, `SECURE_PROXY_SSL_HEADER`, HSTS (1 ano, subdomínios), cookies `Secure`, `Referrer-Policy`, `X-Frame-Options: DENY`, `nosniff` |
| Banco de dados | `DATABASE_URL` interna do Render; nenhuma porta pública exposta; senhas só como hash |
| Informações internas | Erros 500 com mensagem genérica; painel Django em `ADMIN_URL` (padrão `painel-admin/`); logs sem senhas/tokens |
| Abuso | Limite de requisições por IP, mais rígido em login/cadastro/recuperação de senha |
| CORS | Só as origens listadas em `CORS_ALLOWED_ORIGINS` |

> **Nunca** cole `SECRET_KEY`, `DATABASE_URL` ou senhas em prints para o relatório. No painel do Render, mostre apenas os **nomes** das variáveis.

Se uma credencial vazar no GitHub, **troque-a imediatamente** (nova `SECRET_KEY`, nova senha do banco) — apagar o commit não basta, pois o histórico fica público.

## 6. Demonstração (roteiro de ~5 minutos)

1. **Contexto (30 s):** o que é a API, de onde veio (PI3) e por que foi refeita em Django.
2. **Documentação (1 min):** abra `/api/docs` na URL pública; mostre tags, parâmetros, exemplos e códigos de resposta de um endpoint.
3. **Autenticação (1 min):** cadastre um usuário, faça login, use **Authorize**, chame `/usuarios/me`; mostre o **401** sem token.
4. **CRUD (1 min):** crie, liste, atualize e exclua uma mensagem; mostre o **400** de validação (serviço inválido) e o **404**.
5. **Autorização (30 s):** com o usuário comum, tente `POST /depoimentos` ou `GET /admin/usuarios` → **403**; com o ADMIN, funciona.
6. **Hospedagem e segurança (1 min):** HTTPS no navegador, variáveis de ambiente no painel (sem valores), `check --deploy`.
7. **Testes (30 s):** `python -m pytest` (140 testes) e a tabela do `smoke_publico.md`.

Tenha um plano B: vídeo curto do fluxo completo e o relatório de testes aberto.

## 7. Atualizar a API depois de publicada

Cada `git push` na branch conectada dispara um novo deploy automático. Mudanças em modelos exigem `python manage.py makemigrations` localmente e o commit da pasta `migrations/` — o `build.sh` aplica as migrações.
