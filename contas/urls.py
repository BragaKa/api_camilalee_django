from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter(trailing_slash=False)
router.register("admin/usuarios", views.AdminUsuarioViewSet, basename="admin-usuarios")
router.register("admin/logins", views.HistoricoLoginViewSet, basename="admin-logins")

urlpatterns = [
    path("auth/cadastro", views.CadastroView.as_view(), name="auth-cadastro"),
    path("auth/login", views.LoginView.as_view(), name="auth-login"),
    path("auth/refresh", views.RenovarTokenView.as_view(), name="auth-refresh"),
    path("auth/logout", views.LogoutView.as_view(), name="auth-logout"),
    path("auth/esqueci-senha", views.EsqueciSenhaView.as_view(), name="auth-esqueci-senha"),
    path("auth/redefinir-senha", views.RedefinirSenhaView.as_view(), name="auth-redefinir-senha"),
    path("usuarios/me", views.MeView.as_view(), name="usuarios-me"),
] + router.urls
