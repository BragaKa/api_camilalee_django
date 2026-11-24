"""
Configurações do projeto Camila Lee API.

Todas as configurações sensíveis ou que variam entre ambientes (SECRET_KEY,
DEBUG, ALLOWED_HOSTS, banco de dados, e-mail, CORS...) são lidas de VARIÁVEIS
DE AMBIENTE (ou de um arquivo .env local, que NÃO deve ir para o GitHub).
Veja o arquivo .env.example para a lista completa.

Padrões seguros: se nada for informado, DEBUG=False e as proteções de HTTPS
ficam ligadas. Para desenvolver localmente, copie .env.example para .env.
"""
import warnings
from datetime import timedelta
from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
# Lê o .env local, se existir (em produção as variáveis vêm do provedor).
environ.Env.read_env(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# Segurança básica
# ---------------------------------------------------------------------------
DEBUG = env.bool("DEBUG", default=False)

SECRET_KEY = env("SECRET_KEY", default="")
if not SECRET_KEY:
    if DEBUG:
        # Chave apenas para desenvolvimento local. Nunca é usada com DEBUG=False.
        SECRET_KEY = "dev-only-nao-use-em-producao-" + "x" * 40
    else:
        raise ImproperlyConfigured(
            "Defina a variável de ambiente SECRET_KEY (obrigatória com DEBUG=False)."
        )

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1", "[::1]"] if DEBUG else [],
)
# O Render informa o domínio público automaticamente nesta variável.
_render_host = env("RENDER_EXTERNAL_HOSTNAME", default="")
if _render_host and _render_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_render_host)

CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
if _render_host:
    CSRF_TRUSTED_ORIGINS.append(f"https://{_render_host}")

# ---------------------------------------------------------------------------
# Aplicações
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Terceiros
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "corsheaders",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    # Projeto
    "contas",
    "mensagens",
    "depoimentos",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Caminho do painel administrativo do Django (troque em produção para não
# ficar no endereço previsível /admin/).
ADMIN_URL = env("ADMIN_URL", default="painel-admin/").strip("/") + "/"

# ---------------------------------------------------------------------------
# Banco de dados
# Local: SQLite (padrão). Produção: PostgreSQL/MySQL via DATABASE_URL, por
# exemplo  postgres://usuario:senha@host:5432/camilalee
# A URL contém a senha do banco, por isso fica só em variável de ambiente.
# ---------------------------------------------------------------------------
DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
}
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=60)
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Autenticação e senhas
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "contas.Usuario"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("JWT_ACCESS_MINUTES", default=30)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_DAYS", default=1)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    # Assina os tokens com a SECRET_KEY (que vem de variável de ambiente).
    "SIGNING_KEY": SECRET_KEY,
}

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    # Seguro por padrão: todo endpoint exige login, salvo se declarar AllowAny.
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_PAGINATION_CLASS": "common.pagination.PaginacaoPadrao",
    "PAGE_SIZE": 10,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "common.exceptions.tratador_de_excecoes",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/min",
        "user": "240/min",
        # Limites mais rígidos nos endpoints sensíveis (força bruta).
        "login": "10/min",
        "cadastro": "20/hour",
        "esqueci_senha": "5/hour",
        "redefinir_senha": "10/hour",
    },
    # Quantos proxies existem na frente da aplicação (Render = 1). Necessário
    # para identificar corretamente o IP do cliente (throttling e histórico).
    "NUM_PROXIES": env.int("NUM_PROXIES", default=None),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Camila Lee API",
    "DESCRIPTION": (
        "API REST do site da profissional Camila Lee (Crocodilo Lee), "
        "reimplementada em **Python/Django REST Framework** para a disciplina "
        "Programação para Internet (TSI/IFB).\n\n"
        "## Como autenticar\n"
        "1. Cadastre-se em `POST /api/auth/cadastro` (ou use uma conta existente).\n"
        "2. Faça login em `POST /api/auth/login` e copie o valor de `access`.\n"
        "3. Clique em **Authorize** (cadeado) e cole o token. O Swagger envia o "
        "cabeçalho `Authorization: Bearer <token>` nas próximas chamadas.\n\n"
        "## Perfis\n"
        "- `USUARIO`: acessa e gerencia apenas as próprias mensagens e o próprio cadastro.\n"
        "- `ADMIN`: gerencia depoimentos, usuários e consulta o histórico de logins.\n\n"
        "## Formato dos erros\n"
        "Todas as respostas de erro seguem o formato "
        '`{"status": 400, "erro": "Requisição inválida", "mensagem": "...", '
        '"detalhes": {"campo": ["motivo"]}}`.\n\n'
        "## Limites de uso\n"
        "Login, cadastro e recuperação de senha têm limite de requisições por IP "
        "(HTTP 429 quando excedido)."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
    "SWAGGER_UI_SETTINGS": {
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "docExpansion": "list",
    },
    "TAGS": [
        {"name": "Autenticação", "description": "Cadastro, login, renovação de token, logout e recuperação de senha."},
        {"name": "Usuários", "description": "Dados do usuário autenticado."},
        {"name": "Mensagens", "description": "Formulário de contato / solicitação de serviços (exige login)."},
        {"name": "Depoimentos", "description": "Depoimentos de clientes (leitura pública; escrita só ADMIN)."},
        {"name": "Administração", "description": "Gestão de usuários e histórico de logins (somente ADMIN)."},
        {"name": "Sistema", "description": "Verificação de disponibilidade."},
    ],
}

# ---------------------------------------------------------------------------
# CORS (front-end React)
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:5173", "http://localhost:3000"] if DEBUG else [],
)

# ---------------------------------------------------------------------------
# E-mail (recuperação de senha)
# Sem EMAIL_HOST configurado, o e-mail é apenas impresso no log (útil em
# desenvolvimento). Em produção, configure um provedor SMTP.
# ---------------------------------------------------------------------------
EMAIL_HOST = env("EMAIL_HOST", default="")
if EMAIL_HOST:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_PORT = env.int("EMAIL_PORT", default=587)
    EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
    EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
    EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="Camila Lee <nao-responda@camilalee.local>")
CODIGO_REDEFINICAO_MINUTOS = env.int("CODIGO_REDEFINICAO_MINUTOS", default=15)

# ---------------------------------------------------------------------------
# Internacionalização
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Arquivos estáticos (Swagger UI, painel admin) servidos pelo WhiteNoise
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# Em desenvolvimento a pasta só existe depois do collectstatic; evita o aviso.
warnings.filterwarnings("ignore", message="No directory at")
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

# ---------------------------------------------------------------------------
# HTTPS e cabeçalhos de segurança (ativos quando DEBUG=False)
# Verifique com:  python manage.py check --deploy
# ---------------------------------------------------------------------------
# Atrás do proxy do provedor, o HTTPS é indicado por este cabeçalho.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=not DEBUG)
# O health check do provedor chega por HTTP interno: não deve ser redirecionado.
SECURE_REDIRECT_EXEMPT = [r"^api/saude$"]
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=0 if DEBUG else 31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
# Preload é um compromisso difícil de desfazer; fica desligado de propósito
# (o aviso security.W021 do check --deploy é conhecido e justificado).
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# ---------------------------------------------------------------------------
# Logs (nunca registrar senhas/tokens)
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO")},
}
