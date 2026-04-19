# Stage 1: Build frontend assets
FROM docker.io/oven/bun:1 AS frontend-builder

WORKDIR /build

COPY package.json bun.lock ./
# Limit network concurrency to avoid Podman gvproxy bottleneck on macOS.
# Not needed with OrbStack/Docker Desktop, but harmless there (2s vs 135s on Podman).
RUN bun install --frozen-lockfile --network-concurrency 4

COPY app/static/js/ ./app/static/js/
COPY app/static/css/ ./app/static/css/
COPY app/templates/ ./app/templates/
COPY vite.config.js ./

RUN bun run build


# Stage 2: Python application
FROM docker.io/python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/usr/local

WORKDIR /mantis

# Connect to other container via postgres client
RUN apt-get update && \
    apt-get install -y --no-install-recommends postgresql-client && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install dependencies (uv sync with system Python)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application and install project
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY run.py entrypoint.sh ./
COPY --from=frontend-builder /build/app/static/build/ ./app/static/build/

RUN uv sync --frozen --no-dev && \
    chmod +x entrypoint.sh

ENV FLASK_APP=run.py
EXPOSE 5000

ENTRYPOINT ["./entrypoint.sh"]
