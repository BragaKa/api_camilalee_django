from rest_framework import serializers


class ErroSerializer(serializers.Serializer):
    """Formato padrão de todas as respostas de erro da API (usado na documentação)."""

    status = serializers.IntegerField(help_text="Código HTTP do erro.")
    erro = serializers.CharField(help_text="Título curto do erro.")
    mensagem = serializers.CharField(help_text="Explicação legível do problema.")
    detalhes = serializers.DictField(
        required=False,
        help_text="Erros por campo (somente em erros de validação).",
    )
