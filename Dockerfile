# syntax=docker/dockerfile:1.4
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

# Instala dependências Python (usa cache do pip no build para acelerar rebuilds)
COPY requirements.txt /app/
RUN --mount=type=cache,target=/root/.cache/pip \
    PIP_NO_CACHE_DIR=0 pip install --upgrade pip && \
    pip install -r requirements.txt

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
    DB_WAIT_TIMEOUT=90 \
    GUNICORN_WORKER_CLASS=sync \
    GUNICORN_THREADS=1 \
    GUNICORN_KEEP_ALIVE=2 \
    GUNICORN_GRACEFUL_TIMEOUT=30 \
    GUNICORN_MAX_REQUESTS=0 \
    GUNICORN_MAX_REQUESTS_JITTER=0 \
    GUNICORN_PRELOAD=0

CMD ["/bin/sh", "-c", \
    "python scripts/wait_for_db.py && \
     python manage.py migrate --noinput && \
     gunicorn core.wsgi:application \
       --bind 0.0.0.0:8000 \
       --workers ${WEB_CONCURRENCY} \
       --worker-class ${GUNICORN_WORKER_CLASS} \
       --threads ${GUNICORN_THREADS} \
       --timeout ${GUNICORN_TIMEOUT} \
       --keep-alive ${GUNICORN_KEEP_ALIVE} \
       --graceful-timeout ${GUNICORN_GRACEFUL_TIMEOUT} \
       --max-requests ${GUNICORN_MAX_REQUESTS} \
       --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER} \
       --preload=${GUNICORN_PRELOAD} \
       --access-logfile - --error-logfile -"]
