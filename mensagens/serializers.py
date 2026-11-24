from rest_framework import serializers

from common.fields import ModelSerializerEstrito

from .models import Mensagem, Servico

OPCOES_SERVICO = ", ".join(valor for valor, _ in Servico.choices)


class MensagemSerializer(ModelSerializerEstrito):
    usuario_id = serializers.IntegerField(read_only=True, help_text="Quem enviou a mensagem.")
    usuario_nome = serializers.CharField(source="usuario.nome", read_only=True)

    class Meta:
        model = Mensagem
        fields = ["id", "servico", "mensagem", "enviado_em", "usuario_id", "usuario_nome"]
        read_only_fields = ["id", "enviado_em"]
        extra_kwargs = {
            "servico": {
                "error_messages": {
                    "invalid_choice": f"Serviço inválido. Use um destes valores: {OPCOES_SERVICO}.",
                    "required": "Informe o serviço de interesse.",
                },
                "help_text": f"Serviço de interesse: {OPCOES_SERVICO}.",
            },
            "mensagem": {
                "max_length": 1000,
                "help_text": "Texto da mensagem (até 1000 caracteres).",
            },
        }
