from drf_spectacular.utils import OpenApiExample, extend_schema, extend_schema_view
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from common.docs import ERRO_400, ERRO_401, ERRO_404
from .filters import MensagemFilter
from .models import Mensagem
from .serializers import MensagemSerializer

TAG = ["Mensagens"]
AUTH = "\n\n**Autenticação:** exige `Bearer` token."

EXEMPLO = {
    "id": 12,
    "servico": "NOIVAS",
    "mensagem": "Olá! Gostaria de um orçamento de maquiagem e penteado para 14/03.",
    "enviado_em": "2026-11-24T18:45:00-03:00",
    "usuario_id": 7,
    "usuario_nome": "Maria Souza",
}
REQUISICAO = {
    "servico": "NOIVAS",
    "mensagem": "Olá! Gostaria de um orçamento de maquiagem e penteado para 14/03.",
}


@extend_schema_view(
    list=extend_schema(
        tags=TAG,
        summary="Listar mensagens",
        description=(
            "Lista paginada. Um `USUARIO` vê só as próprias mensagens; um `ADMIN` vê todas.\n\n"
            "Filtros: `servico`, `usuario` (id), `data_inicio`, `data_fim` (AAAA-MM-DD). "
            "Busca (`search`) no texto da mensagem ou no nome do remetente. "
            "Ordenação (`ordering`): `enviado_em`, `servico`, `id` (prefixe com `-` para decrescente). "
            "Paginação: `page` e `page_size` (máx. 100)." + AUTH
        ),
        responses={200: MensagemSerializer(many=True), 401: ERRO_401},
    ),
    create=extend_schema(
        tags=TAG,
        summary="Enviar mensagem",
        description=(
            "Registra uma mensagem/solicitação de serviço. O remetente é sempre o usuário "
            "autenticado (não é enviado no corpo)." + AUTH
        ),
        responses={201: MensagemSerializer, 400: ERRO_400, 401: ERRO_401},
        examples=[
            OpenApiExample("Requisição", value=REQUISICAO, request_only=True),
            OpenApiExample("Mensagem criada", value=EXEMPLO, response_only=True, status_codes=["201"]),
        ],
    ),
    retrieve=extend_schema(
        tags=TAG,
        summary="Consultar uma mensagem",
        description="Retorna 404 se a mensagem não existir ou pertencer a outro usuário (exceto ADMIN)." + AUTH,
        responses={200: MensagemSerializer, 401: ERRO_401, 404: ERRO_404},
        examples=[OpenApiExample("Mensagem", value=EXEMPLO, response_only=True)],
    ),
    update=extend_schema(
        tags=TAG,
        summary="Atualizar mensagem (completo)",
        description="O autor (ou um ADMIN) pode substituir `servico` e `mensagem`." + AUTH,
        responses={200: MensagemSerializer, 400: ERRO_400, 401: ERRO_401, 404: ERRO_404},
        examples=[OpenApiExample("Requisição", value=REQUISICAO, request_only=True)],
    ),
    partial_update=extend_schema(
        tags=TAG,
        summary="Atualizar mensagem (parcial)",
        description="Altera apenas os campos enviados." + AUTH,
        responses={200: MensagemSerializer, 400: ERRO_400, 401: ERRO_401, 404: ERRO_404},
        examples=[OpenApiExample("Requisição", value={"servico": "AUDIOVISUAL"}, request_only=True)],
    ),
    destroy=extend_schema(
        tags=TAG,
        summary="Excluir mensagem",
        description="O autor (ou um ADMIN) pode excluir." + AUTH,
        responses={204: None, 401: ERRO_401, 404: ERRO_404},
    ),
)
class MensagemViewSet(viewsets.ModelViewSet):
    serializer_class = MensagemSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = MensagemFilter
    search_fields = ["mensagem", "usuario__nome"]
    ordering_fields = ["enviado_em", "servico", "id"]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):  # geração do esquema OpenAPI
            return Mensagem.objects.none()
        consulta = Mensagem.objects.select_related("usuario")
        if not self.request.user.eh_admin:
            # Isolamento: cada usuário só enxerga (e altera) o que é seu.
            consulta = consulta.filter(usuario=self.request.user)
        return consulta.order_by("-enviado_em", "-id")

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)
