from django.http import JsonResponse
from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class SaudeView(APIView):
    """Endpoint leve usado pelo provedor de hospedagem (health check)."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = []

    @extend_schema(
        tags=["Sistema"],
        summary="Verifica se a API está no ar",
        description="Não exige autenticação. Retorna HTTP 200 quando a aplicação responde.",
        responses={
            200: inline_serializer("Saude", {"status": serializers.CharField()}),
        },
        examples=[OpenApiExample("API disponível", value={"status": "ok"}, response_only=True)],
    )
    def get(self, request):
        return Response({"status": "ok"})


def erro_404(request, exception=None):
    return JsonResponse(
        {"status": 404, "erro": "Não encontrado", "mensagem": "O endereço solicitado não existe."},
        status=404,
    )


def erro_500(request):
    # Mensagem genérica: nunca expõe detalhes internos da aplicação.
    return JsonResponse(
        {
            "status": 500,
            "erro": "Erro interno do servidor",
            "mensagem": "Ocorreu um erro inesperado. Tente novamente mais tarde.",
        },
        status=500,
    )
