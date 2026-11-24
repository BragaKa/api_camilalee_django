import django_filters

from .models import Mensagem


class MensagemFilter(django_filters.FilterSet):
    data_inicio = django_filters.DateFilter(
        field_name="enviado_em", lookup_expr="date__gte", help_text="AAAA-MM-DD (inclusive)."
    )
    data_fim = django_filters.DateFilter(
        field_name="enviado_em", lookup_expr="date__lte", help_text="AAAA-MM-DD (inclusive)."
    )

    class Meta:
        model = Mensagem
        fields = ["servico", "usuario", "data_inicio", "data_fim"]
