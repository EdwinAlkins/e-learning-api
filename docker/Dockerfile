#########################
# builder Stage
#########################
FROM python:3.13-slim-trixie AS builder

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    # git=1:2.47.3-0+deb13u1 \
    libpq-dev=17.9-0+deb13u1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY --from=ghcr.io/astral-sh/uv:0.11.3 /uv /uvx /bin/

# .git est exclu du contexte Docker ; setuptools-scm a besoin d'une version explicite.
# `git describe --tags --always` sans tag renvoie un hash seul (ex. e7f1aa2), invalide en PEP 440 :
# on le préfixe alors en version locale (0.0.0+<hash>).
ARG VERSION=0.0.0-dev
COPY pyproject.toml ./
COPY . .

RUN uv venv --python 3.13 /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv pip install --upgrade pip
RUN RAW_VER="${VERSION}" && \
    if printf '%s' "$RAW_VER" | grep -qE '^[0-9a-f]{7,40}$'; then \
      export SETUPTOOLS_SCM_PRETEND_VERSION="0.0.0+${RAW_VER}"; \
    else \
      export SETUPTOOLS_SCM_PRETEND_VERSION="$RAW_VER"; \
    fi && \
    uv pip install .

#########################
# API Stage
#########################
FROM python:3.13-slim-trixie AS api

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    libpq5=17.9-0+deb13u1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 10001 e_learning_group \
    && useradd --system --uid 10001 --gid e_learning_group e_learning_user

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY --chown=e_learning_user:e_learning_group src ./src

USER e_learning_user

CMD [ "python", "-m", "src.api" ]