from rest_framework.permissions import BasePermission


class EhAdmin(BasePermission):
    """Permite acesso apenas a usuários autenticados com o perfil ADMIN."""

    message = "Acesso restrito a administradores."

    def has_permission(self, request, view):
        usuario = request.user
        return bool(usuario and usuario.is_authenticated and usuario.eh_admin)
