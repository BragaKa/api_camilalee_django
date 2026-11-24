from common.fields import ModelSerializerEstrito

from .models import Depoimento


class DepoimentoSerializer(ModelSerializerEstrito):
    class Meta:
        model = Depoimento
        fields = ["id", "nome_autor", "profissao", "texto", "criado_em"]
        read_only_fields = ["id", "criado_em"]
        extra_kwargs = {
            "nome_autor": {"help_text": "Nome do cliente (até 120 caracteres)."},
            "profissao": {"help_text": "Profissão ou qualificação, ex.: Noiva, Atriz."},
            "texto": {"help_text": "Conteúdo do depoimento (até 2000 caracteres)."},
        }
