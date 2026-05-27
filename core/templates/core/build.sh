#!/usr/bin/env bash
# sai do script imediatamente se algum comando falhar
set -o errexit

# Instala as dependências do Python
pip install -r requirements.txt

# Coleta os arquivos de CSS/JS para uma pasta centralizada de produção
python manage.py collectstatic --no-input

# Aplica as migrações do banco de dados se houver alguma pendente
python manage.py migrate