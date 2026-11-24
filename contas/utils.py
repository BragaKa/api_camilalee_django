"""Utilitários do histórico de logins (IP e informações do User-Agent)."""
import re

from rest_framework.throttling import BaseThrottle


def obter_ip(request):
    """IP do cliente respeitando NUM_PROXIES (evita confiar em X-Forwarded-For forjado)."""
    return BaseThrottle().get_ident(request)[:45]


def analisar_user_agent(user_agent):
    """Extrai sistema operacional, navegador e tipo de dispositivo do User-Agent."""
    ua = user_agent or ""

    if re.search(r"Windows", ua):
        so = "Windows"
    elif re.search(r"Android", ua):
        so = "Android"
    elif re.search(r"iPhone|iPad|iPod", ua):
        so = "iOS"
    elif re.search(r"Macintosh|Mac OS X", ua):
        so = "macOS"
    elif re.search(r"Linux|X11", ua):
        so = "Linux"
    else:
        so = "Desconhecido"

    # A ordem importa: o Edge e o Opera também dizem "Chrome" no User-Agent.
    if re.search(r"Edg/|Edge/", ua):
        navegador = "Edge"
    elif re.search(r"OPR/|Opera", ua):
        navegador = "Opera"
    elif re.search(r"Firefox/", ua):
        navegador = "Firefox"
    elif re.search(r"Chrome/|CriOS/", ua):
        navegador = "Chrome"
    elif re.search(r"Safari/", ua):
        navegador = "Safari"
    elif ua:
        navegador = "Outro"
    else:
        navegador = "Desconhecido"

    if re.search(r"iPad|Tablet", ua):
        dispositivo = "Tablet"
    elif re.search(r"Mobi|iPhone|Android", ua):
        dispositivo = "Celular"
    elif ua:
        dispositivo = "Computador"
    else:
        dispositivo = "Desconhecido"

    return so, navegador, dispositivo
