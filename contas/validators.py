import re

from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth import password_validation
from rest_framework import serializers

# Aceita formatos como: 61999999999, (61) 99999-9999, +55 61 99999-9999
_CARACTERES_PERMITIDOS = re.compile(r"^\+?[\d\s().-]+$")


def validar_telefone(valor):
    """Telefone brasileiro: DDD + 8 ou 9 dígitos, com ou sem o código do país (55)."""
    valor = valor.strip()
    if not _CARACTERES_PERMITIDOS.match(valor):
        raise serializers.ValidationError(
            "Telefone inválido: use apenas números, espaços, parênteses, hífen e o sinal +."
        )
    digitos = re.sub(r"\D", "", valor)
    if digitos.startswith("55") and len(digitos) in (12, 13):
        digitos = digitos[2:]
    if len(digitos) not in (10, 11):
        raise serializers.ValidationError(
            "Telefone inválido: informe o DDD e o número (10 ou 11 dígitos)."
        )
    return valor


def validar_senha_forte(senha, usuario=None):
    """Aplica os validadores de senha do Django (tamanho mínimo, senhas comuns...)."""
    try:
        password_validation.validate_password(senha, user=usuario)
    except DjangoValidationError as erro:
        raise serializers.ValidationError(list(erro.messages))
    return senha
