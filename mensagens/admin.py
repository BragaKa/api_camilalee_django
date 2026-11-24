from django.contrib import admin

from .models import Mensagem


@admin.register(Mensagem)
class MensagemAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "servico", "enviado_em")
    list_filter = ("servico",)
    search_fields = ("mensagem", "usuario__nome", "usuario__email")
