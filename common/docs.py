"""Respostas de erro reutilizáveis na documentação OpenAPI (Swagger)."""
from drf_spectacular.utils import OpenApiExample, OpenApiResponse

from .serializers import ErroSerializer


def _erro(descricao, nome, valor):
    return OpenApiResponse(
        response=ErroSerializer,
        description=descricao,
        examples=[OpenApiExample(nome, value=valor, response_only=True)],
    )


ERRO_400 = _erro(
    "Requisição inválida: campo obrigatório ausente, tipo incorreto ou valor fora das regras.",
    "Erro de validação",
    {
        "status": 400,
        "erro": "Requisição inválida",
        "mensagem": "Os dados enviados são inválidos.",
        "detalhes": {"campo": ["Este campo é obrigatório."]},
    },
)
ERRO_401 = _erro(
    "Não autenticado: token ausente, inválido ou expirado.",
    "Sem token",
    {
        "status": 401,
        "erro": "Não autenticado",
        "mensagem": "As credenciais de autenticação não foram fornecidas.",
    },
)
ERRO_403 = _erro(
    "Acesso negado: o usuário autenticado não tem permissão (perfil insuficiente).",
    "Perfil insuficiente",
    {
        "status": 403,
        "erro": "Acesso negado",
        "mensagem": "Acesso restrito a administradores.",
    },
)
ERRO_404 = _erro(
    "Registro inexistente (ou que não pertence ao usuário autenticado).",
    "Registro inexistente",
    {"status": 404, "erro": "Não encontrado", "mensagem": "Não encontrado."},
)
ERRO_409 = _erro(
    "Conflito: o recurso já existe.",
    "E-mail duplicado",
    {
        "status": 409,
        "erro": "Conflito",
        "mensagem": "Já existe um usuário cadastrado com este e-mail.",
    },
)
ERRO_429 = _erro(
    "Muitas requisições: limite de uso por IP excedido (veja o cabeçalho Retry-After).",
    "Limite excedido",
    {
        "status": 429,
        "erro": "Muitas requisições",
        "mensagem": "Pedido foi limitado (throttled). Disponível novamente em 42 segundos.",
    },
)
