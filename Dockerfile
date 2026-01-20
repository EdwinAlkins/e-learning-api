#########################
# builder Stage
#########################
FROM python:3.13-slim-bookworm AS builder

# Variables d'environnement pour la sécurité et les performances
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Installation des dépendances système nécessaires pour la compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Installation de uv depuis la release officielle
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copie des fichiers de dépendances et du code source
COPY pyproject.toml ./
COPY uv.lock* ./
COPY src ./src

# Création de l'environnement virtuel et installation des dépendances
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv sync --frozen || uv sync && \
    uv pip install -e .

#########################
# Runtime Stage
#########################
FROM python:3.13-slim-bookworm AS runtime

# Variables d'environnement pour la sécurité
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH"

# Création d'un utilisateur non-root pour la sécurité
RUN groupadd -r appuser && \
    useradd -r -g appuser -u 1000 -d /app -s /bin/bash appuser && \
    mkdir -p /app/data /app/videos && \
    chown -R appuser:appuser /app

# Installation de uv dans le runtime stage (nécessaire pour installer le package)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copie de l'environnement virtuel depuis le builder
COPY --from=builder /opt/venv /opt/venv

# Définition du répertoire de travail
WORKDIR /app

# Copie du code source et des fichiers de configuration
COPY --chown=appuser:appuser pyproject.toml ./
COPY --chown=appuser:appuser src ./src
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser alembic ./alembic

# Installation du package en mode éditable (doit être fait en tant que root)
USER root
RUN . /opt/venv/bin/activate && uv pip install -e .
USER appuser

# Exposition du port
EXPOSE 8000

# Point d'entrée par défaut
CMD ["python", "-m", "src.api"]
