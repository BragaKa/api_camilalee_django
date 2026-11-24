import django_filters

from .models import HistoricoLogin, Usuario


class UsuarioFilter(django_filters.FilterSet):
    perfil = django_filters.CharFilter(
        field_name="perfil__nome", lookup_expr="iexact", help_text="ADMIN ou USUARIO."
    )

    class Meta:
        model = Usuario
        fields = ["perfil", "is_active"]


class HistoricoLoginFilter(django_filters.FilterSet):
    data_inicio = django_filters.DateFilter(
        field_name="data_hora", lookup_expr="date__gte", help_text="AAAA-MM-DD (inclusive)."
    )
    data_fim = django_filters.DateFilter(
        field_name="data_hora", lookup_expr="date__lte", help_text="AAAA-MM-DD (inclusive)."
    )

    class Meta:
        model = HistoricoLogin
        fields = ["status", "usuario", "data_inicio", "data_fim"]
