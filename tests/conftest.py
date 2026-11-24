"""Fixtures compartilhadas pelos testes automatizados."""
import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from contas.models import Perfil, Usuario

from .helpers import SENHA, cliente_de


@pytest.fixture(autouse=True)
def limpar_cache():
    """O limite de requisições (throttling) usa cache: zera a cada teste."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def hash_rapido(settings):
    """Troca o hash de senha por um rápido, só nos testes (o real é o PBKDF2)."""
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture
def api():
    return APIClient()


@pytest.fixture
def criar_usuario(db):
    def _criar(email="maria@email.com", nome="Maria Souza", telefone="61999999999",
               senha=SENHA, admin=False, **extra):
        perfil = Perfil.objects.get(nome=Perfil.ADMIN if admin else Perfil.USUARIO)
        return Usuario.objects.create_user(
            email=email, password=senha, nome=nome, telefone=telefone, perfil=perfil, **extra
        )

    return _criar


@pytest.fixture
def usuario(criar_usuario):
    return criar_usuario()


@pytest.fixture
def outro_usuario(criar_usuario):
    return criar_usuario(email="joao@email.com", nome="João Lima", telefone="61988887777")


@pytest.fixture
def admin(criar_usuario):
    return criar_usuario(email="camila@email.com", nome="Camila Lee", admin=True)


@pytest.fixture
def api_usuario(usuario):
    return cliente_de(usuario)


@pytest.fixture
def api_outro(outro_usuario):
    return cliente_de(outro_usuario)


@pytest.fixture
def api_admin(admin):
    return cliente_de(admin)
