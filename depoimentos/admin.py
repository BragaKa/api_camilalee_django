from django.contrib import admin

from .models import Depoimento


@admin.register(Depoimento)
class DepoimentoAdmin(admin.ModelAdmin):
    list_display = ("id", "nome_autor", "profissao", "criado_em")
    search_fields = ("nome_autor", "profissao", "texto")
