#!/usr/bin/env bash
# Script de build usado pelo Render (e útil em qualquer hospedagem Python).
set -o errexit   # interrompe no primeiro erro

pip install -r requirements.txt

# Reúne os arquivos estáticos (Swagger UI, painel admin) servidos pelo WhiteNoise.
python manage.py collectstatic --no-input

# Cria/atualiza as tabelas do banco.
python manage.py migrate --no-input

# Cria o usuário ADMIN se ADMIN_EMAIL e ADMIN_SENHA estiverem definidos (idempotente).
python manage.py criar_admin
