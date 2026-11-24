from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from common.docs import ERRO_400, ERRO_401, ERRO_403, ERRO_404
from common.permissions import EhAdmin

from .filters import DepoimentoFilter
from .models import Depoimento
from .serializers import DepoimentoSerializer

TAG = ["Depoimentos"]
SO_ADMIN = "\n\n**Autenticação:** exige `Bearer` token de um usuário **ADMIN**."

EXEMPLO = {
    "id": 3,
    "nome_autor": "Ana Paula",
    "profissao": "Noiva",
    "texto": "Atendimento incrível! Minha maquiagem durou a festa inteira.",
    "criado_em": "2026-11-24T18:50:00-03:00",
}
REQUISICAO = {
    "nome_autor": "Ana Paula",
    "profissao": "Noiva",
    "texto": "Atendimento incrível! Minha maquiagem durou a festa inteira.",
}


@extend_schema_view(
    list=extend_schema(
        tags=TAG,
        summary="Listar depoimentos",
        description=(
            "Lista paginada, **pública** (não exige autenticação).\n\n"
            "Filtros: `profissao` (contém), `data_inicio`, `data_fim` (AAAA-MM-DD). "
            "Busca (`search`) em nome, profissão ou texto. "
            "Ordenação (`ordering`): `criado_em`, `nome_autor`, `id`. "
            "Paginação: `page` e `page_size` (máx. 100)."
        ),
        responses={200: DepoimentoSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=TAG,
        summary="Consultar um depoimento",
        description="Público (não exige autenticação).",
        responses={200: DepoimentoSerializer, 404: ERRO_404},
        examples=[OpenApiExample("Depoimento", value=EXEMPLO, response_only=True)],
    ),
    create=extend_schema(
        tags=TAG,
        summary="Cadastrar depoimento",
        description="Somente ADMIN." + SO_ADMIN,
        responses={201: DepoimentoSerializer, 400: ERRO_400, 401: ERRO_401, 403: ERRO_403},
        examples=[
            OpenApiExample("Requisição", value=REQUISICAO, request_only=True),
            OpenApiExample("Depoimento criado", value=EXEMPLO, response_only=True, status_codes=["201"]),
        ],
    ),
    update=extend_schema(
        tags=TAG,
        summary="Atualizar depoimento (completo)",
        description="Somente ADMIN." + SO_ADMIN,
        responses={200: DepoimentoSerializer, 400: ERRO_400, 401: ERRO_401, 403: ERRO_403, 404: ERRO_404},
        examples=[OpenApiExample("Requisição", value=REQUISICAO, request_only=True)],
    ),
    partial_update=extend_schema(
        tags=TAG,
        summary="Atualizar depoimento (parcial)",
        description="Somente ADMIN." + SO_ADMIN,
        responses={200: DepoimentoSerializer, 400: ERRO_400, 401: ERRO_401, 403: ERRO_403, 404: ERRO_404},
        examples=[OpenApiExample("Requisição", value={"profissao": "Atriz"}, request_only=True)],
    ),
    destroy=extend_schema(
        tags=TAG,
        summary="Excluir depoimento",
        description="Somente ADMIN." + SO_ADMIN,
        responses={204: None, 401: ERRO_401, 403: ERRO_403, 404: ERRO_404},
    ),
)
class DepoimentoViewSet(viewsets.ModelViewSet):
    queryset = Depoimento.objects.all()
    serializer_class = DepoimentoSerializer
    filterset_class = DepoimentoFilter
    search_fields = ["nome_autor", "profissao", "texto"]
    ordering_fields = ["criado_em", "nome_autor", "id"]

    def get_permissions(self):
        # Leitura pública; escrita restrita ao perfil ADMIN.
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        return [EhAdmin()]
