# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=core.settings

WORKDIR /app

# Dependências de SO mínimas (somente runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Instala dependências Python
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copia o código
COPY . /app

# Cria usuário não-root para rodar a app
RUN adduser --disabled-login --gecos "" --home /app appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Aguarda DB, aplica migrações e inicia o servidor WSGI
# Logs no stdout/err e timeout adequado
ENV WEB_CONCURRENCY=2 \
    GUNICORN_TIMEOUT=60 \
    DB_WAIT_TIMEOUT=90

CMD ["/bin/sh", "-c", \
     "python scripts/wait_for_db.py && \
      python manage.py migrate --noinput && \
      gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers ${WEB_CONCURRENCY} --timeout ${GUNICORN_TIMEOUT} --access-logfile - --error-logfile -"]
