#########################
# builder Stage
#########################
FROM python:3.12-slim-bookworm AS builder

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    git \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY . .
RUN uv venv --python 3.12 /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN uv pip install --upgrade pip
RUN uv pip install .

#########################
# API Stage
#########################
FROM python:3.12-slim-bookworm AS api

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    libpq5 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY src ./src

CMD [ "python", "-m", "src.api" ]