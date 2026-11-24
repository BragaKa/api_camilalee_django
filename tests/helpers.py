"""Funções auxiliares usadas pelos testes."""
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

SENHA = "Senha@Forte2026"


def cliente_de(usuario):
    """Cliente HTTP já autenticado com um token JWT válido do usuário."""
    cliente = APIClient()
    token = RefreshToken.for_user(usuario).access_token
    cliente.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return cliente


def verificar_erro(resposta, status):
    """Confere o formato padrão de erro da API e devolve o corpo."""
    assert resposta.status_code == status, resposta.content
    corpo = resposta.json()
    assert corpo["status"] == status
    assert corpo["erro"] and corpo["mensagem"]
    return corpo
