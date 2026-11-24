import django_filters

from .models import Depoimento


class DepoimentoFilter(django_filters.FilterSet):
    profissao = django_filters.CharFilter(
        lookup_expr="icontains", help_text="Parte da profissão (sem diferenciar maiúsculas)."
    )
    data_inicio = django_filters.DateFilter(
        field_name="criado_em", lookup_expr="date__gte", help_text="AAAA-MM-DD (inclusive)."
    )
    data_fim = django_filters.DateFilter(
        field_name="criado_em", lookup_expr="date__lte", help_text="AAAA-MM-DD (inclusive)."
    )

    class Meta:
        model = Depoimento
        fields = ["profissao", "data_inicio", "data_fim"]
