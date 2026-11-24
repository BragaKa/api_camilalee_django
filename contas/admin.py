from django.contrib import admin

from .models import CodigoRedefinicaoSenha, HistoricoLogin, Perfil, Usuario


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("id", "nome")


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ("id", "nome", "email", "perfil", "is_active", "criado_em")
    list_filter = ("perfil", "is_active")
    search_fields = ("nome", "email")
    exclude = ("password", "groups", "user_permissions")  # nunca exibe o hash da senha


@admin.register(HistoricoLogin)
class HistoricoLoginAdmin(admin.ModelAdmin):
    list_display = ("data_hora", "usuario", "status", "ip", "navegador", "sistema_operacional")
    list_filter = ("status",)
    readonly_fields = [f.name for f in HistoricoLogin._meta.fields]

    def has_add_permission(self, request):
        return False


@admin.register(CodigoRedefinicaoSenha)
class CodigoRedefinicaoSenhaAdmin(admin.ModelAdmin):
    list_display = ("email", "expira_em", "utilizado")
    exclude = ("codigo",)  # o código é segredo: não aparece no painel
    readonly_fields = ("email", "expira_em", "utilizado")

    def has_add_permission(self, request):
        return False
