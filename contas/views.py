"""Endpoints de autenticação, perfil do usuário e administração."""
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.db.models import Count, Max, Q
from django.utils import timezone
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from common.docs import ERRO_400, ERRO_401, ERRO_403, ERRO_404, ERRO_409, ERRO_429
from common.exceptions import Conflito, CredenciaisInvalidas
from common.permissions import EhAdmin

from .filters import HistoricoLoginFilter, UsuarioFilter
from .models import CodigoRedefinicaoSenha, HistoricoLogin, Perfil, Usuario
from .serializers import (
    AdminUsuarioSerializer,
    CadastroSerializer,
    EsqueciSenhaSerializer,
    HistoricoLoginSerializer,
    LoginRespostaSerializer,
    LoginSerializer,
    LogoutSerializer,
    MensagemSimplesSerializer,
    RedefinirSenhaSerializer,
    ResumoLoginsSerializer,
    TokensRenovadosSerializer,
    UsuarioAtualizacaoSerializer,
    UsuarioSerializer,
)
from .utils import analisar_user_agent, obter_ip

logger = logging.getLogger(__name__)

TAG_AUTH = ["Autenticação"]
TAG_USUARIOS = ["Usuários"]
TAG_ADMIN = ["Administração"]

EXEMPLO_USUARIO = {
    "id": 7,
    "nome": "Maria Souza",
    "email": "maria@email.com",
    "telefone": "61999999999",
    "perfil": "USUARIO",
    "criado_em": "2026-11-24T18:30:00-03:00",
}


# ---------------------------------------------------------------------------
# Autenticação
# ---------------------------------------------------------------------------
class CadastroView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = "cadastro"

    @extend_schema(
        tags=TAG_AUTH,
        summary="Cadastrar usuário",
        description=(
            "Cria uma conta com perfil `USUARIO`. A senha é armazenada apenas como hash. "
            "O perfil não pode ser escolhido pelo cliente (somente um ADMIN altera perfis).\n\n"
            "**Autenticação:** não exige token."
        ),
        request=CadastroSerializer,
        responses={
            201: UsuarioSerializer,
            400: ERRO_400,
            409: ERRO_409,
            429: ERRO_429,
        },
        examples=[
            OpenApiExample(
                "Requisição",
                value={
                    "nome": "Maria Souza",
                    "email": "maria@email.com",
                    "telefone": "61999999999",
                    "senha": "Senha@Forte2026",
                },
                request_only=True,
            ),
            OpenApiExample("Usuário criado", value=EXEMPLO_USUARIO, response_only=True, status_codes=["201"]),
        ],
    )
    def post(self, request):
        serializer = CadastroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dados = serializer.validated_data

        mensagem_conflito = "Já existe um usuário cadastrado com este e-mail."
        if Usuario.objects.filter(email=dados["email"]).exists():
            raise Conflito(mensagem_conflito)
        try:
            with transaction.atomic():
                usuario = Usuario.objects.create_user(
                    email=dados["email"],
                    password=dados["senha"],
                    nome=dados["nome"],
                    telefone=dados["telefone"],
                )
        except IntegrityError:  # duas requisições simultâneas com o mesmo e-mail
            raise Conflito(mensagem_conflito)
        return Response(UsuarioSerializer(usuario).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = "login"

    @extend_schema(
        tags=TAG_AUTH,
        summary="Fazer login",
        description=(
            "Valida e-mail e senha e devolve os tokens JWT. Cada tentativa (com sucesso ou "
            "falha) é registrada no histórico de logins (IP, sistema, navegador, dispositivo).\n\n"
            "**Autenticação:** não exige token. Limite: 10 tentativas por minuto por IP."
        ),
        request=LoginSerializer,
        responses={
            200: LoginRespostaSerializer,
            400: ERRO_400,
            401: ERRO_401,
            429: ERRO_429,
        },
        examples=[
            OpenApiExample(
                "Requisição",
                value={"email": "maria@email.com", "senha": "Senha@Forte2026"},
                request_only=True,
            ),
            OpenApiExample(
                "Login realizado",
                value={
                    "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "Bearer",
                    "expires_in": 1800,
                    "usuario": EXEMPLO_USUARIO,
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "Credenciais inválidas",
                value={
                    "status": 401,
                    "erro": "Não autenticado",
                    "mensagem": "E-mail ou senha inválidos.",
                },
                response_only=True,
                status_codes=["401"],
            ),
        ],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        usuario = authenticate(request, email=email, password=serializer.validated_data["senha"])
        self._registrar(request, email, usuario)
        if usuario is None:
            raise CredenciaisInvalidas()

        update_last_login(None, usuario)
        refresh = RefreshToken.for_user(usuario)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "token_type": "Bearer",
                "expires_in": int(jwt_settings.ACCESS_TOKEN_LIFETIME.total_seconds()),
                "usuario": UsuarioSerializer(usuario).data,
            }
        )

    @staticmethod
    def _registrar(request, email, usuario):
        so, navegador, dispositivo = analisar_user_agent(request.META.get("HTTP_USER_AGENT", ""))
        alvo = usuario or Usuario.objects.filter(email=email).first()
        HistoricoLogin.objects.create(
            usuario=alvo,
            ip=obter_ip(request),
            sistema_operacional=so,
            navegador=navegador,
            dispositivo=dispositivo,
            localizacao="Não identificada",
            status=HistoricoLogin.Status.SUCESSO if usuario else HistoricoLogin.Status.FALHA,
        )


@extend_schema_view(
    post=extend_schema(
        tags=TAG_AUTH,
        summary="Renovar token de acesso",
        description=(
            "Troca um token `refresh` válido por um novo par `access`/`refresh`. O `refresh` "
            "antigo é invalidado (rotação de tokens).\n\n**Autenticação:** não exige token de acesso."
        ),
        responses={
            200: TokensRenovadosSerializer,
            401: ERRO_401,
        },
        examples=[
            OpenApiExample("Requisição", value={"refresh": "eyJhbGciOi..."}, request_only=True),
            OpenApiExample(
                "Tokens renovados",
                value={"access": "eyJhbGciOi...", "refresh": "eyJhbGciOi..."},
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
)
class RenovarTokenView(TokenRefreshView):
    pass


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=TAG_AUTH,
        summary="Encerrar sessão (logout)",
        description=(
            "Invalida o token `refresh` informado (lista de bloqueio). O token de acesso "
            "atual expira sozinho em poucos minutos.\n\n**Autenticação:** exige `Bearer` token."
        ),
        request=LogoutSerializer,
        responses={204: None, 400: ERRO_400, 401: ERRO_401},
        examples=[OpenApiExample("Requisição", value={"refresh": "eyJhbGciOi..."}, request_only=True)],
    )
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
        except TokenError:
            raise serializers.ValidationError(
                {"refresh": ["Token de atualização inválido, expirado ou já utilizado."]}
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


class EsqueciSenhaView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = "esqueci_senha"

    @extend_schema(
        tags=TAG_AUTH,
        summary="Solicitar código de recuperação de senha",
        description=(
            "Envia por e-mail um código de 6 dígitos (uso único, validade de 15 minutos). "
            "A resposta é **sempre a mesma**, exista ou não o e-mail, para não revelar quais "
            "contas existem.\n\n**Autenticação:** não exige token. Limite: 5 por hora por IP."
        ),
        request=EsqueciSenhaSerializer,
        responses={200: MensagemSimplesSerializer, 400: ERRO_400, 429: ERRO_429},
        examples=[
            OpenApiExample("Requisição", value={"email": "maria@email.com"}, request_only=True),
            OpenApiExample(
                "Resposta",
                value={"mensagem": "Se o e-mail estiver cadastrado, enviaremos um código de 6 dígitos."},
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def post(self, request):
        serializer = EsqueciSenhaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        usuario = Usuario.objects.filter(email=email, is_active=True).first()
        if usuario:
            # Invalida códigos anteriores ainda não usados.
            CodigoRedefinicaoSenha.objects.filter(email=email, utilizado=False).update(utilizado=True)
            codigo = f"{secrets.randbelow(10**6):06d}"
            CodigoRedefinicaoSenha.objects.create(
                email=email,
                codigo=codigo,
                expira_em=timezone.now() + timedelta(minutes=settings.CODIGO_REDEFINICAO_MINUTOS),
            )
            try:
                send_mail(
                    subject="Camila Lee - código para redefinir sua senha",
                    message=(
                        f"Olá, {usuario.nome}!\n\nSeu código de verificação é: {codigo}\n"
                        f"Ele vale por {settings.CODIGO_REDEFINICAO_MINUTOS} minutos e só pode ser "
                        "usado uma vez.\nSe não foi você, ignore esta mensagem."
                    ),
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                )
            except Exception:  # falha de SMTP não deve revelar se o e-mail existe
                logger.exception("Falha ao enviar o e-mail de redefinição de senha")
        return Response(
            {"mensagem": "Se o e-mail estiver cadastrado, enviaremos um código de 6 dígitos."}
        )


class RedefinirSenhaView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = "redefinir_senha"

    @extend_schema(
        tags=TAG_AUTH,
        summary="Redefinir a senha com o código recebido",
        description=(
            "Define uma nova senha usando o código de 6 dígitos enviado por e-mail. O código só "
            "vale uma vez e expira. Após a troca, todos os tokens `refresh` do usuário são "
            "invalidados.\n\n**Autenticação:** não exige token. Limite: 10 por hora por IP."
        ),
        request=RedefinirSenhaSerializer,
        responses={200: MensagemSimplesSerializer, 400: ERRO_400, 429: ERRO_429},
        examples=[
            OpenApiExample(
                "Requisição",
                value={
                    "email": "maria@email.com",
                    "codigo": "482913",
                    "nova_senha": "NovaSenha@2026",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Senha redefinida",
                value={"mensagem": "Senha redefinida com sucesso."},
                response_only=True,
                status_codes=["200"],
            ),
        ],
    )
    def post(self, request):
        serializer = RedefinirSenhaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dados = serializer.validated_data

        registro = (
            CodigoRedefinicaoSenha.objects.filter(
                email=dados["email"],
                codigo=dados["codigo"],
                utilizado=False,
                expira_em__gt=timezone.now(),
            )
            .order_by("-id")
            .first()
        )
        usuario = Usuario.objects.filter(email=dados["email"], is_active=True).first()
        if registro is None or usuario is None:
            raise serializers.ValidationError({"codigo": ["Código inválido ou expirado."]})

        with transaction.atomic():
            usuario.set_password(dados["nova_senha"])
            usuario.save(update_fields=["password"])
            registro.utilizado = True
            registro.save(update_fields=["utilizado"])
            # Encerra todas as sessões abertas (tokens refresh) desse usuário.
            for token in OutstandingToken.objects.filter(user=usuario):
                BlacklistedToken.objects.get_or_create(token=token)
        return Response({"mensagem": "Senha redefinida com sucesso."})


# ---------------------------------------------------------------------------
# Usuário autenticado
# ---------------------------------------------------------------------------
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=TAG_USUARIOS,
        summary="Consultar o próprio perfil",
        description="**Autenticação:** exige `Bearer` token.",
        responses={200: UsuarioSerializer, 401: ERRO_401},
        examples=[OpenApiExample("Usuário", value=EXEMPLO_USUARIO, response_only=True)],
    )
    def get(self, request):
        return Response(UsuarioSerializer(request.user).data)

    @extend_schema(
        tags=TAG_USUARIOS,
        summary="Atualizar o próprio cadastro (completo)",
        description="Substitui `nome` e `telefone`. O e-mail e o perfil não podem ser alterados.\n\n"
        "**Autenticação:** exige `Bearer` token.",
        request=UsuarioAtualizacaoSerializer,
        responses={200: UsuarioSerializer, 400: ERRO_400, 401: ERRO_401},
        examples=[
            OpenApiExample(
                "Requisição",
                value={"nome": "Maria S. Souza", "telefone": "(61) 98888-7777"},
                request_only=True,
            )
        ],
    )
    def put(self, request):
        return self._atualizar(request, parcial=False)

    @extend_schema(
        tags=TAG_USUARIOS,
        summary="Atualizar o próprio cadastro (parcial)",
        description="Altera apenas os campos enviados.\n\n**Autenticação:** exige `Bearer` token.",
        request=UsuarioAtualizacaoSerializer,
        responses={200: UsuarioSerializer, 400: ERRO_400, 401: ERRO_401},
        examples=[OpenApiExample("Requisição", value={"telefone": "61988887777"}, request_only=True)],
    )
    def patch(self, request):
        return self._atualizar(request, parcial=True)

    @extend_schema(
        tags=TAG_USUARIOS,
        summary="Excluir a própria conta",
        description=(
            "Remove a conta e as mensagens do usuário. O histórico de logins é mantido, sem "
            "vínculo com o usuário.\n\n**Autenticação:** exige `Bearer` token."
        ),
        responses={204: None, 401: ERRO_401},
    )
    def delete(self, request):
        request.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _atualizar(self, request, parcial):
        serializer = UsuarioAtualizacaoSerializer(request.user, data=request.data, partial=parcial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UsuarioSerializer(request.user).data)


# ---------------------------------------------------------------------------
# Administração (somente perfil ADMIN)
# ---------------------------------------------------------------------------
@extend_schema_view(
    list=extend_schema(
        tags=TAG_ADMIN,
        summary="Listar usuários",
        description=(
            "Lista paginada de usuários. Filtros: `perfil`, `is_active`. Busca (`search`) por "
            "nome ou e-mail. Ordenação (`ordering`): `nome`, `email`, `criado_em`, `id` "
            "(prefixe com `-` para decrescente).\n\n**Autenticação:** exige `Bearer` token de ADMIN."
        ),
        responses={200: AdminUsuarioSerializer(many=True), 401: ERRO_401, 403: ERRO_403},
    ),
    retrieve=extend_schema(
        tags=TAG_ADMIN,
        summary="Consultar um usuário",
        description="**Autenticação:** exige `Bearer` token de ADMIN.",
        responses={200: AdminUsuarioSerializer, 401: ERRO_401, 403: ERRO_403, 404: ERRO_404},
    ),
    update=extend_schema(
        tags=TAG_ADMIN,
        summary="Atualizar um usuário (completo)",
        description=(
            "Altera nome, telefone, perfil e situação (`is_active`). O e-mail não é editável. "
            "Um ADMIN não pode rebaixar o próprio perfil.\n\n**Autenticação:** exige `Bearer` token de ADMIN."
        ),
        responses={200: AdminUsuarioSerializer, 400: ERRO_400, 401: ERRO_401, 403: ERRO_403, 404: ERRO_404},
        examples=[
            OpenApiExample(
                "Requisição",
                value={
                    "nome": "Maria Souza",
                    "telefone": "61999999999",
                    "perfil": "ADMIN",
                    "is_active": True,
                },
                request_only=True,
            )
        ],
    ),
    partial_update=extend_schema(
        tags=TAG_ADMIN,
        summary="Atualizar um usuário (parcial)",
        description="**Autenticação:** exige `Bearer` token de ADMIN.",
        responses={200: AdminUsuarioSerializer, 400: ERRO_400, 401: ERRO_401, 403: ERRO_403, 404: ERRO_404},
        examples=[OpenApiExample("Promover a ADMIN", value={"perfil": "ADMIN"}, request_only=True)],
    ),
    destroy=extend_schema(
        tags=TAG_ADMIN,
        summary="Excluir um usuário",
        description=(
            "Remove o usuário e suas mensagens. Um ADMIN não pode excluir a si mesmo por aqui "
            "(use `DELETE /api/usuarios/me`).\n\n**Autenticação:** exige `Bearer` token de ADMIN."
        ),
        responses={204: None, 400: ERRO_400, 401: ERRO_401, 403: ERRO_403, 404: ERRO_404},
    ),
)
class AdminUsuarioViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = AdminUsuarioSerializer
    permission_classes = [EhAdmin]
    queryset = Usuario.objects.select_related("perfil").order_by("id")
    filterset_class = UsuarioFilter
    search_fields = ["nome", "email"]
    ordering_fields = ["id", "nome", "email", "criado_em"]

    def perform_update(self, serializer):
        novo_perfil = serializer.validated_data.get("perfil")
        if (
            serializer.instance == self.request.user
            and novo_perfil is not None
            and novo_perfil.nome != Perfil.ADMIN
        ):
            raise serializers.ValidationError({"perfil": ["Você não pode rebaixar o próprio perfil."]})
        serializer.save()

    def perform_destroy(self, instance):
        if instance == self.request.user:
            raise serializers.ValidationError(
                {"id": ["Você não pode excluir a própria conta por este endpoint."]}
            )
        instance.delete()


@extend_schema_view(
    list=extend_schema(
        tags=TAG_ADMIN,
        summary="Listar o histórico de logins",
        description=(
            "Lista paginada dos acessos (sucessos e falhas). Filtros: `status` (SUCESSO/FALHA), "
            "`usuario` (id), `data_inicio` e `data_fim` (AAAA-MM-DD). Busca (`search`) por nome, "
            "e-mail, IP, navegador ou sistema. Ordenação (`ordering`): `data_hora`, `status`.\n\n"
            "**Autenticação:** exige `Bearer` token de ADMIN."
        ),
        responses={200: HistoricoLoginSerializer(many=True), 401: ERRO_401, 403: ERRO_403},
    ),
)
class HistoricoLoginViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = HistoricoLoginSerializer
    permission_classes = [EhAdmin]
    queryset = HistoricoLogin.objects.select_related("usuario").order_by("-data_hora")
    filterset_class = HistoricoLoginFilter
    search_fields = ["usuario__nome", "usuario__email", "ip", "navegador", "sistema_operacional"]
    ordering_fields = ["data_hora", "status"]

    @extend_schema(
        tags=TAG_ADMIN,
        summary="Indicadores de acesso",
        description=(
            "Totais de logins, sucessos, falhas e último acesso bem-sucedido no período "
            "(padrão: 30 dias).\n\n**Autenticação:** exige `Bearer` token de ADMIN."
        ),
        parameters=[
            OpenApiParameter(
                "dias", int, description="Período em dias (1 a 365). Padrão: 30.", default=30
            )
        ],
        responses={200: ResumoLoginsSerializer, 400: ERRO_400, 401: ERRO_401, 403: ERRO_403},
        examples=[
            OpenApiExample(
                "Resumo",
                value={
                    "periodo_dias": 30,
                    "total_logins": 42,
                    "logins_realizados": 38,
                    "falhas_de_login": 4,
                    "ultimo_acesso": "2026-11-24T18:30:00-03:00",
                },
                response_only=True,
            )
        ],
    )
    @action(detail=False, methods=["get"], filter_backends=[], pagination_class=None)
    def resumo(self, request):
        bruto = request.query_params.get("dias", "30")
        try:
            dias = int(bruto)
            if not 1 <= dias <= 365:
                raise ValueError
        except ValueError:
            raise serializers.ValidationError({"dias": ["Informe um número inteiro entre 1 e 365."]})

        inicio = timezone.now() - timedelta(days=dias)
        dados = HistoricoLogin.objects.filter(data_hora__gte=inicio).aggregate(
            total=Count("id"),
            sucessos=Count("id", filter=Q(status=HistoricoLogin.Status.SUCESSO)),
            falhas=Count("id", filter=Q(status=HistoricoLogin.Status.FALHA)),
            ultimo=Max("data_hora", filter=Q(status=HistoricoLogin.Status.SUCESSO)),
        )
        return Response(
            {
                "periodo_dias": dias,
                "total_logins": dados["total"],
                "logins_realizados": dados["sucessos"],
                "falhas_de_login": dados["falhas"],
                "ultimo_acesso": dados["ultimo"],
            }
        )
