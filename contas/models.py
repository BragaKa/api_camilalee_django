"""
Modelos do domínio de contas, espelhando o dicionário de dados do relatório do
Projeto Integrador (tabelas perfis, usuarios, codigos_redefinicao_senha e
historico_logins). Os nomes de tabelas e colunas (db_table / db_column) seguem
o modelo físico original; o atributo Python continua se chamando `id`.
"""
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils import timezone


class Perfil(models.Model):
    ADMIN = "ADMIN"
    USUARIO = "USUARIO"

    id = models.BigAutoField(primary_key=True, db_column="id_perfil")
    nome = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = "perfis"
        ordering = ["id"]

    def __str__(self):
        return self.nome


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def _perfil(self, nome):
        perfil, _ = Perfil.objects.get_or_create(nome=nome)
        return perfil

    def create_user(self, email, password, nome, telefone, perfil=None, **extra):
        if not email:
            raise ValueError("O e-mail é obrigatório.")
        usuario = self.model(
            email=self.normalize_email(email).lower(),
            nome=nome,
            telefone=telefone,
            perfil=perfil or self._perfil(Perfil.USUARIO),
            **extra,
        )
        usuario.set_password(password)  # grava apenas o hash da senha
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email, password, nome, telefone, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(
            email, password, nome, telefone, perfil=self._perfil(Perfil.ADMIN), **extra
        )


class Usuario(AbstractBaseUser, PermissionsMixin):
    id = models.BigAutoField(primary_key=True, db_column="id_usuario")
    perfil = models.ForeignKey(
        Perfil, on_delete=models.PROTECT, related_name="usuarios", db_column="id_perfil"
    )
    nome = models.CharField(max_length=120)
    email = models.EmailField(max_length=180, unique=True)
    telefone = models.CharField(max_length=30)
    # Substitui o campo `password` do Django para manter a coluna `senha`.
    password = models.CharField(max_length=255, db_column="senha")
    criado_em = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)  # acesso ao painel Django admin

    objects = UsuarioManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nome", "telefone"]

    class Meta:
        db_table = "usuarios"
        ordering = ["id"]

    def __str__(self):
        return f"{self.nome} <{self.email}>"

    @property
    def eh_admin(self):
        return self.perfil.nome == Perfil.ADMIN


class CodigoRedefinicaoSenha(models.Model):
    """Código de 6 dígitos, de uso único e com prazo de validade."""

    id = models.BigAutoField(primary_key=True)
    email = models.CharField(max_length=255, db_index=True)
    codigo = models.CharField(max_length=6)
    expira_em = models.DateTimeField()
    utilizado = models.BooleanField(default=False)

    class Meta:
        db_table = "codigos_redefinicao_senha"

    def __str__(self):
        return f"código para {self.email} (utilizado={self.utilizado})"


class HistoricoLogin(models.Model):
    class Status(models.TextChoices):
        SUCESSO = "SUCESSO", "Sucesso"
        FALHA = "FALHA", "Falha"

    id = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey(
        Usuario,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,  # o histórico sobrevive à exclusão do usuário
        related_name="historico_logins",
        db_column="id_usuario",
    )
    ip = models.CharField(max_length=45, blank=True, default="")
    sistema_operacional = models.CharField(max_length=100, blank=True, default="")
    navegador = models.CharField(max_length=100, blank=True, default="")
    dispositivo = models.CharField(max_length=150, blank=True, default="")
    localizacao = models.CharField(max_length=150, blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices)
    data_hora = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "historico_logins"
        ordering = ["-data_hora"]

    def __str__(self):
        return f"{self.status} em {self.data_hora:%d/%m/%Y %H:%M}"
