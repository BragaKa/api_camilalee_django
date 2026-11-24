"""Cadastra os perfis de acesso (equivale ao INSERT INTO perfis do modelo físico)."""
from django.db import migrations


def criar_perfis(apps, schema_editor):
    Perfil = apps.get_model("contas", "Perfil")
    for nome in ("ADMIN", "USUARIO"):
        Perfil.objects.get_or_create(nome=nome)


class Migration(migrations.Migration):
    dependencies = [("contas", "0001_initial")]

    operations = [migrations.RunPython(criar_perfis, migrations.RunPython.noop)]
