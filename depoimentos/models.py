from django.db import models
from django.utils import timezone


class Depoimento(models.Model):
    """Depoimento de cliente exibido no site (independente dos demais cadastros)."""

    id = models.BigAutoField(primary_key=True, db_column="id_depoimento")
    nome_autor = models.CharField(max_length=120)
    profissao = models.CharField(max_length=120)
    texto = models.CharField(max_length=2000)
    criado_em = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "depoimentos"
        ordering = ["-criado_em", "-id"]

    def __str__(self):
        return f"{self.nome_autor} ({self.profissao})"
