# Camila Lee API — Python / Django REST Framework

API REST do site da profissional **Camila Lee (Crocodilo Lee)**, reimplementada em **Python com Django REST Framework** como **Projeto Final** da disciplina **Programação para Internet** (TSI/IFB).

Ela expande e reproduz, em Python, o domínio da API desenvolvida no Projeto Integrador III (Java/Spring Boot): usuários e perfis, login com JWT, mensagens de contato, depoimentos, recuperação de senha e histórico de logins. O projeto original em Java **não é alterado** — este repositório é independente.

- **Documentação interativa (Swagger UI):** `/api/docs` · **ReDoc:** `/api/redoc` · **Esquema OpenAPI:** `/api/schema` (cópia em [`docs/openapi.yaml`](docs/openapi.yaml))
- **Relatório de testes:** [`docs/RELATORIO_DE_TESTES.md`](docs/RELATORIO_DE_TESTES.md)
- **Publicação (hospedagem):** [`docs/DEPLOY.md`](docs/DEPLOY.md)
- **URL pública da API:** _preencha aqui depois de publicar_ → `https://SUA-API.onrender.com/api/docs`

## Tecnologias

| Item | Uso |
|---|---|
| Python 3.13 · Django 5.2 (LTS) | Framework web e ORM |
| Django REST Framework | Serializers, ViewSets, permissões, paginação, filtros |
| Simple JWT | Autenticação por token (access + refresh, com lista de bloqueio no logout) |
| drf-spectacular (+ sidecar) | Documentação OpenAPI / Swagger UI / ReDoc |
| django-filter | Filtros por campo, período, busca e ordenação |
| django-environ | Configuração por variáveis de ambiente (`.env`) |
| WhiteNoise · gunicorn | Arquivos estáticos e servidor de produção |
| SQLite (local) · PostgreSQL (produção) | Banco de dados via `DATABASE_URL` |
| pytest · pytest-django | Testes automatizados |

## Estrutura

```
api_camilalee_django/
├── config/          # settings (tudo por variável de ambiente), urls, wsgi
├── common/          # código compartilhado: erros padronizados, permissões, paginação, docs
├── contas/          # Perfil, Usuário, códigos de redefinição, histórico de logins + auth + admin
├── mensagens/       # Mensagem (formulário de contato / solicitação de serviço)
├── depoimentos/     # Depoimento
├── tests/           # 140 testes automatizados (pytest)
├── scripts/         # smoke_test.py (testa qualquer URL) e gerar_relatorio_testes.py
├── docs/            # DEPLOY.md, RELATORIO_DE_TESTES.md, openapi.yaml, evidencias/
├── build.sh · render.yaml · requirements*.txt · .env.example · pytest.ini
```

## Como instalar e executar (local)

Pré-requisito: **Python 3.10 ou superior** (testado com 3.13).

**Windows (PowerShell)**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env          # abra o .env e confira DEBUG=True
python manage.py migrate
python manage.py createsuperuser     # cria um ADMIN (pede e-mail, nome, telefone e senha)
python manage.py runserver
```

**Linux / macOS**
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Abra **http://127.0.0.1:8000/api/docs**. Sem configurar nada além do `.env`, o banco é um arquivo SQLite local (`db.sqlite3`).
O `createsuperuser` já cria o usuário com perfil **ADMIN**. Usuários comuns se cadastram em `POST /api/auth/cadastro`.

> Em `DEBUG=True` o e-mail de recuperação de senha aparece **no terminal** (o código de 6 dígitos), sem precisar de SMTP.

## Como usar a autenticação (Swagger)

1. `POST /api/auth/cadastro` com nome, e-mail, telefone e senha → **201**.
2. `POST /api/auth/login` → copie o valor de `access`.
3. Clique em **Authorize** (cadeado), cole o token e confirme. As rotas com cadeado passam a funcionar.
4. Quando o `access` expirar (30 min), use `POST /api/auth/refresh` com o `refresh`.

Exemplo com `curl` (Linux/macOS/Git Bash):
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login -H "Content-Type: application/json" \
     -d '{"email":"maria@email.com","senha":"Senha@Forte2026"}'
curl http://127.0.0.1:8000/api/usuarios/me -H "Authorization: Bearer SEU_ACCESS_TOKEN"
```

## Endpoints

Todos sob `/api`. **Acesso:** 🌐 público · 🔑 usuário autenticado · 🛡️ somente ADMIN.

| Método | Rota | Descrição | Acesso |
|---|---|---|---|
| POST | `/auth/cadastro` | Cadastrar usuário (perfil USUARIO) | 🌐 |
| POST | `/auth/login` | Login → tokens JWT (registra histórico) | 🌐 |
| POST | `/auth/refresh` | Renovar token | 🌐 |
| POST | `/auth/logout` | Invalidar o refresh token | 🔑 |
| POST | `/auth/esqueci-senha` | Enviar código de 6 dígitos por e-mail | 🌐 |
| POST | `/auth/redefinir-senha` | Trocar a senha com o código | 🌐 |
| GET · PUT · PATCH · DELETE | `/usuarios/me` | Ver, editar e excluir a própria conta | 🔑 |
| GET · POST | `/mensagens` | Listar (só as suas; ADMIN vê todas) · enviar | 🔑 |
| GET · PUT · PATCH · DELETE | `/mensagens/{id}` | Consultar, editar, excluir (dono ou ADMIN) | 🔑 |
| GET | `/depoimentos` · `/depoimentos/{id}` | Listar e consultar depoimentos | 🌐 |
| POST · PUT · PATCH · DELETE | `/depoimentos[/{id}]` | Gerenciar depoimentos | 🛡️ |
| GET | `/admin/usuarios` | Listar usuários (filtros, busca, ordenação) | 🛡️ |
| GET · PUT · PATCH · DELETE | `/admin/usuarios/{id}` | Consultar, alterar perfil/situação, excluir | 🛡️ |
| GET | `/admin/logins` | Histórico de logins | 🛡️ |
| GET | `/admin/logins/resumo` | Indicadores de acesso (padrão: 30 dias) | 🛡️ |
| GET | `/saude` | Health check | 🌐 |

**Listagens** aceitam `?page=` e `?page_size=` (máx. 100), `?search=`, `?ordering=campo` (ou `-campo`) e filtros específicos
(`servico`, `data_inicio`, `data_fim`, `profissao`, `status`, `perfil`…). Veja todos os parâmetros no Swagger.

**Serviços aceitos nas mensagens:** `NOIVAS`, `AUDIOVISUAL`, `CORTE_CABELO`, `CARACTERIZACAO`, `OUTROS`.

## Validação e erros

Dados são validados antes de chegar ao banco: campos obrigatórios, tipos (um número no lugar de texto é rejeitado), e-mail, telefone brasileiro, tamanho máximo, força da senha, serviço dentro da enumeração e valores de filtro. Todo erro usa o mesmo formato:

```json
{
  "status": 400,
  "erro": "Requisição inválida",
  "mensagem": "Os dados enviados são inválidos.",
  "detalhes": { "email": ["Insira um endereço de email válido."] }
}
```

| Código | Quando |
|---|---|
| 400 | Validação, JSON malformado, parâmetro inválido |
| 401 | Sem token, token inválido/expirado, login incorreto |
| 403 | Autenticado, mas sem perfil suficiente (ex.: USUARIO em rota de ADMIN) |
| 404 | Registro inexistente (ou de outro usuário) · rota inexistente |
| 405 / 415 | Método não permitido · corpo que não é JSON |
| 409 | E-mail já cadastrado |
| 429 | Limite de requisições excedido (login, cadastro, recuperação de senha) |
| 500 | Erro interno, sempre com mensagem genérica |

## Testes

```bash
python -m pytest                                   # 140 testes automatizados
python scripts/smoke_test.py http://127.0.0.1:8000 # testa uma API em execução (ou a URL pública)
python scripts/gerar_relatorio_testes.py           # regenera docs/RELATORIO_DE_TESTES.md
```

O `smoke_test.py` aceita `--admin-email` e `--admin-senha` para incluir os cenários de ADMIN e grava uma tabela *esperado × obtido* que entra no relatório. Detalhes e resultados em [`docs/RELATORIO_DE_TESTES.md`](docs/RELATORIO_DE_TESTES.md).

## Hospedagem e segurança

O repositório já traz `render.yaml` e `build.sh` para publicar no **Render** (passo a passo em [`docs/DEPLOY.md`](docs/DEPLOY.md)). Resumo do que a rubrica pede:

- `DEBUG=False` por padrão; `ALLOWED_HOSTS` por variável de ambiente.
- `SECRET_KEY`, `DATABASE_URL`, senha do ADMIN e e-mail só em variáveis de ambiente — a aplicação **não inicia** sem `SECRET_KEY` quando `DEBUG=False`. O `.env` está no `.gitignore`.
- HTTPS: redirecionamento, HSTS, cookies `Secure` e reconhecimento do proxy do provedor.
- `python manage.py check --deploy` sem avisos, exceto `security.W021` (HSTS *preload*), mantido de propósito — justificativa no relatório.
- Banco acessado pela URL interna do provedor; erros 500 sem detalhes; painel do Django em caminho configurável (`ADMIN_URL`).

### Variáveis de ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `SECRET_KEY` | em produção | Chave do Django e de assinatura dos JWT |
| `DEBUG` | não (padrão `False`) | `True` só no desenvolvimento local |
| `ALLOWED_HOSTS` | em produção* | Domínios aceitos, separados por vírgula (*no Render o domínio é adicionado sozinho) |
| `DATABASE_URL` | em produção | Ex.: `postgres://usuario:senha@host:5432/banco`. Vazio = SQLite local |
| `CORS_ALLOWED_ORIGINS` | se houver front-end | Origens do front-end autorizadas |
| `NUM_PROXIES` | em produção | Nº de proxies à frente da aplicação (Render = `1`) |
| `ADMIN_EMAIL`, `ADMIN_SENHA` | opcional | Cria o ADMIN no deploy (`python manage.py criar_admin`) |
| `EMAIL_HOST`, `EMAIL_PORT`, … | opcional | SMTP para a recuperação de senha |

Lista completa e comentada em [`.env.example`](.env.example).

## Diferenças em relação à API Java do PI3

| Tema | API Java (PI3) | Esta API (Django) | Motivo |
|---|---|---|---|
| Token JWT | Cookie HttpOnly + token CSRF (`X-XSRF-TOKEN`) | Cabeçalho `Authorization: Bearer` | Funciona direto no Swagger/Postman e dispensa CSRF; o front passa a guardar o token |
| Hash de senha | Hash via Spring Security | PBKDF2-SHA256 (padrão do Django) | Padrão do framework; a senha nunca é guardada em texto puro |
| Cadastro | `POST /auth/cadastro` | `POST /api/auth/cadastro` | Mesmo caminho, sob o prefixo `/api` |
| Validação do telefone | `@ValidPhoneNumber` (Java) | Validador próprio (DDD + 8/9 dígitos, com ou sem +55) | Regra escrita do zero em Python; confira se bate com o `PhoneNumberValidator.java` |
| Enum `Servico` | Valores do relatório do PI | `NOIVAS`, `AUDIOVISUAL`, `CORTE_CABELO`, `CARACTERIZACAO`, `OUTROS` | Igual ao relatório |
| Status do login | Enum `StatusLogin` | `SUCESSO` / `FALHA` | Valores assumidos a partir do painel (logins realizados × falhas); confira com o enum Java |
| Tabelas e colunas | `perfis`, `usuarios`, `mensagem`, `depoimentos`, `codigos_redefinicao_senha`, `historico_logins` | Mesmos nomes (`db_table` / `db_column`) | Compatível com o dicionário de dados do relatório; `usuarios` ganha colunas do sistema de login do Django (`is_active`, `is_staff`, `is_superuser`, `last_login`) |

## Mapa da rubrica

| Critério | Onde está |
|---|---|
| 1. CRUD e funcionamento | `mensagens/`, `depoimentos/`, `contas/` (usuários) · testes `tests/test_mensagens.py`, `test_depoimentos.py`, `test_admin.py` |
| 2. Validação e erros | `*/serializers.py`, `common/exceptions.py`, `common/fields.py`, `contas/validators.py` · `tests/test_validacao.py` |
| 3. Autenticação e autorização | `contas/views.py` (JWT), `common/permissions.py`, isolamento em `mensagens/views.py` · `tests/test_auth.py` |
| 4. Documentação | `/api/docs`, `/api/redoc`, `docs/openapi.yaml` (exemplos, parâmetros, códigos HTTP, autenticação) |
| 5. Hospedagem e segurança | `config/settings.py`, `render.yaml`, `build.sh`, `docs/DEPLOY.md` · `check --deploy` no relatório |
| 6. Testes e relatório | `tests/`, `scripts/`, `docs/RELATORIO_DE_TESTES.md`, `docs/evidencias/` |
| 7. Organização e GitHub | Estrutura acima, este README e histórico de commits |
| 8. Apresentação | Roteiro sugerido em `docs/DEPLOY.md` (seção "Demonstração") |

## Limitações conhecidas

- **Limite de requisições (throttling)** usa o cache em memória de cada processo: com 2 *workers* do gunicorn o limite efetivo por IP pode chegar ao dobro. Para um limite exato em vários servidores, troque por Redis ou cache em banco.
- **Código de redefinição de senha** (6 dígitos) é protegido por validade, uso único e limite por IP, mas não bloqueia por e-mail após N erros.
- **E-mail no plano gratuito do Render:** portas SMTP 25, 465 e 587 são bloqueadas; sem outro provedor/porta o código não é entregue (veja `docs/DEPLOY.md`).
- O Swagger UI é público de propósito (exigência da rubrica); ele mostra o contrato da API, não dados.
