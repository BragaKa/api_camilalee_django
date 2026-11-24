"""
Cria (ou promove) o usuário administrador a partir de variáveis de ambiente.

Útil em hospedagens sem acesso ao terminal (ex.: plano gratuito do Render):

    ADMIN_EMAIL=camila@email.com ADMIN_SENHA='...' python manage.py criar_admin

Não faz nada se ADMIN_EMAIL ou ADMIN_SENHA não estiverem definidos, e é seguro
executar várias vezes (idempotente).
"""
import os

from django.core.management.base import BaseCommand

from contas.models import Perfil, Usuario


class Command(BaseCommand):
    help = "Cria o usuário ADMIN usando ADMIN_EMAIL, ADMIN_SENHA, ADMIN_NOME e ADMIN_TELEFONE."

    def handle(self, *args, **options):
        email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
        senha = os.environ.get("ADMIN_SENHA", "")
        if not email or not senha:
            self.stdout.write("ADMIN_EMAIL/ADMIN_SENHA não definidos: nada a fazer.")
            return

        existente = Usuario.objects.filter(email=email).first()
        if existente:
            if not existente.eh_admin:
                existente.perfil = Perfil.objects.get(nome=Perfil.ADMIN)
                existente.save(update_fields=["perfil"])
                self.stdout.write(f"Usuário {email} promovido a ADMIN.")
            else:
                self.stdout.write(f"Usuário {email} já é ADMIN.")
            return

        Usuario.objects.create_superuser(
            email=email,
            password=senha,
            nome=os.environ.get("ADMIN_NOME", "Administradora"),
            telefone=os.environ.get("ADMIN_TELEFONE", "61999999999"),
        )
        self.stdout.write(self.style.SUCCESS(f"Administrador {email} criado."))
