"""Campos de serializer mais rígidos que os padrões do DRF."""
from django.db import models
from rest_framework import serializers


class TextoEstrito(serializers.CharField):
    """
    CharField que só aceita string de verdade. O CharField padrão do DRF converte
    números em texto (ex.: 123 vira "123"), o que esconderia erros de tipo.
    """

    default_error_messages = {"invalid": "Valor inválido: envie um texto (string)."}

    def to_internal_value(self, data):
        if not isinstance(data, str):
            self.fail("invalid")
        return super().to_internal_value(data)


class ModelSerializerEstrito(serializers.ModelSerializer):
    """ModelSerializer que usa TextoEstrito para todos os campos de texto do modelo."""

    serializer_field_mapping = {
        **serializers.ModelSerializer.serializer_field_mapping,
        models.CharField: TextoEstrito,
        models.TextField: TextoEstrito,
    }
