from django.conf import settings
from django.db import models
from django.utils import timezone


class Servico(models.TextChoices):
    """Serviços oferecidos (enumeração Servico do relatório do PI)."""

    NOIVAS = "NOIVAS", "Noivas"
    AUDIOVISUAL = "AUDIOVISUAL", "Audiovisual"
    CORTE_CABELO = "CORTE_CABELO", "Corte de cabelo"
    CARACTERIZACAO = "CARACTERIZACAO", "Caracterização"
    OUTROS = "OUTROS", "Outros"


class Mensagem(models.Model):
    """Mensagem/solicitação de serviço enviada por um usuário autenticado."""

    id = models.BigAutoField(primary_key=True, db_column="id_mensagem")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mensagens",
        db_column="id_usuario",
    )
    servico = models.CharField(max_length=30, choices=Servico.choices)
    mensagem = models.CharField(max_length=1000)
    enviado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "mensagem"
        ordering = ["-enviado_em", "-id"]

    def __str__(self):
        return f"{self.servico} - {self.usuario_id}"
