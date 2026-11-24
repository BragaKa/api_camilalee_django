from rest_framework import serializers

from common.fields import ModelSerializerEstrito, TextoEstrito

from .models import HistoricoLogin, Perfil, Usuario
from .validators import validar_senha_forte, validar_telefone


class UsuarioSerializer(serializers.ModelSerializer):
    """Dados públicos de um usuário (nunca inclui a senha)."""

    perfil = serializers.CharField(source="perfil.nome", read_only=True)

    class Meta:
        model = Usuario
        fields = ["id", "nome", "email", "telefone", "perfil", "criado_em"]
        read_only_fields = fields


class CadastroSerializer(serializers.Serializer):
    nome = TextoEstrito(min_length=2, max_length=120, help_text="Nome completo.")
    email = serializers.EmailField(max_length=180, help_text="Usado como login. Deve ser único.")
    telefone = TextoEstrito(
        max_length=30,
        validators=[validar_telefone],
        help_text="Telefone com DDD, ex.: 61999999999 ou (61) 99999-9999.",
    )
    senha = TextoEstrito(
        write_only=True,
        max_length=128,
        style={"input_type": "password"},
        help_text="Mínimo de 8 caracteres; não pode ser comum nem só numérica.",
    )

    def validate_email(self, valor):
        return valor.strip().lower()

    def validate(self, attrs):
        # Passa um usuário temporário para o validador de similaridade de senha.
        provisorio = Usuario(nome=attrs["nome"], email=attrs["email"])
        validar_senha_forte(attrs["senha"], provisorio)
        return attrs


class UsuarioAtualizacaoSerializer(ModelSerializerEstrito):
    """Atualização dos próprios dados. O e-mail e o perfil não podem ser alterados aqui."""

    class Meta:
        model = Usuario
        fields = ["nome", "telefone"]
        extra_kwargs = {
            "nome": {"min_length": 2},
            "telefone": {"validators": [validar_telefone]},
        }


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=180)
    senha = TextoEstrito(
        write_only=True, max_length=128, style={"input_type": "password"}
    )

    def validate_email(self, valor):
        return valor.strip().lower()


class LoginRespostaSerializer(serializers.Serializer):
    access = serializers.CharField(help_text="Token de acesso (enviar em Authorization: Bearer).")
    refresh = serializers.CharField(help_text="Token para renovar o acesso e para o logout.")
    token_type = serializers.CharField(default="Bearer")
    expires_in = serializers.IntegerField(help_text="Validade do token de acesso, em segundos.")
    usuario = UsuarioSerializer()


class TokensRenovadosSerializer(serializers.Serializer):
    access = serializers.CharField(help_text="Novo token de acesso.")
    refresh = serializers.CharField(help_text="Novo token de atualização (o anterior deixa de valer).")


class LogoutSerializer(serializers.Serializer):
    refresh = TextoEstrito(help_text="Token de atualização a ser invalidado.")


class EsqueciSenhaSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=180)

    def validate_email(self, valor):
        return valor.strip().lower()


class RedefinirSenhaSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=180)
    codigo = serializers.RegexField(
        r"^\d{6}$",
        error_messages={"invalid": "O código deve ter exatamente 6 dígitos."},
        help_text="Código de 6 dígitos recebido por e-mail.",
    )
    nova_senha = TextoEstrito(
        write_only=True, max_length=128, style={"input_type": "password"}
    )

    def validate_email(self, valor):
        return valor.strip().lower()

    def validate(self, attrs):
        validar_senha_forte(attrs["nova_senha"], Usuario(email=attrs["email"]))
        return attrs


class MensagemSimplesSerializer(serializers.Serializer):
    """Resposta padrão com uma mensagem de texto."""

    mensagem = serializers.CharField()


# --------------------------------------------------------------------------
# Administração
# --------------------------------------------------------------------------
class AdminUsuarioSerializer(ModelSerializerEstrito):
    perfil = serializers.SlugRelatedField(
        slug_field="nome",
        queryset=Perfil.objects.all(),
        help_text="ADMIN ou USUARIO.",
    )

    class Meta:
        model = Usuario
        fields = ["id", "nome", "email", "telefone", "perfil", "is_active", "criado_em"]
        read_only_fields = ["id", "email", "criado_em"]
        extra_kwargs = {
            "nome": {"min_length": 2},
            "telefone": {"validators": [validar_telefone]},
        }


class HistoricoLoginSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.CharField(source="usuario.nome", read_only=True, default=None)
    usuario_email = serializers.CharField(source="usuario.email", read_only=True, default=None)

    class Meta:
        model = HistoricoLogin
        fields = [
            "id",
            "usuario",
            "usuario_nome",
            "usuario_email",
            "ip",
            "sistema_operacional",
            "navegador",
            "dispositivo",
            "localizacao",
            "status",
            "data_hora",
        ]
        read_only_fields = fields


class ResumoLoginsSerializer(serializers.Serializer):
    periodo_dias = serializers.IntegerField()
    total_logins = serializers.IntegerField()
    logins_realizados = serializers.IntegerField()
    falhas_de_login = serializers.IntegerField()
    ultimo_acesso = serializers.DateTimeField(allow_null=True)
