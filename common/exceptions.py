"""
Tratamento centralizado de erros.

Toda resposta de erro da API usa o mesmo formato JSON:

    {
      "status": 400,
      "erro": "Requisição inválida",
      "mensagem": "Os dados enviados são inválidos.",
      "detalhes": {"email": ["Informe um endereço de e-mail válido."]}
    }

"detalhes" só aparece nos erros de validação (HTTP 400).
"""
from rest_framework import exceptions
from rest_framework.views import exception_handler

TITULOS = {
    400: "Requisição inválida",
    401: "Não autenticado",
    403: "Acesso negado",
    404: "Não encontrado",
    405: "Método não permitido",
    409: "Conflito",
    415: "Tipo de conteúdo não suportado",
    429: "Muitas requisições",
}


class Conflito(exceptions.APIException):
    """HTTP 409 - ex.: e-mail já cadastrado."""

    status_code = 409
    default_detail = "O recurso já existe."
    default_code = "conflito"


class CredenciaisInvalidas(exceptions.APIException):
    """
    HTTP 401 no login. Não herda de AuthenticationFailed porque, sem o
    cabeçalho WWW-Authenticate, o DRF converteria esse erro em 403.
    """

    status_code = 401
    default_detail = "E-mail ou senha inválidos."
    default_code = "credenciais_invalidas"


def _extrair_mensagem(dados):
    """Obtém um texto simples de qualquer formato de erro do DRF/SimpleJWT."""
    if isinstance(dados, dict):
        if "detail" in dados:
            return str(dados["detail"])
        return "Não foi possível processar a requisição."
    if isinstance(dados, (list, tuple)):
        return " ".join(str(item) for item in dados)
    return str(dados)


def tratador_de_excecoes(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        # Erro inesperado: o Django aciona o handler500 (sem vazar detalhes).
        return None

    codigo = response.status_code
    dados = response.data
    corpo = {"status": codigo, "erro": TITULOS.get(codigo, "Erro")}

    if isinstance(exc, exceptions.ValidationError):
        corpo["mensagem"] = "Os dados enviados são inválidos."
        corpo["detalhes"] = dados if isinstance(dados, dict) else {"non_field_errors": dados}
    elif isinstance(exc, exceptions.ParseError):
        corpo["mensagem"] = "Corpo da requisição inválido: envie um JSON bem formado."
    else:
        corpo["mensagem"] = _extrair_mensagem(dados)

    response.data = corpo
    return response
