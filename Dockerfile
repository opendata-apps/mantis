# Base images are pinned by digest so two builds of the same commit produce
# the same image. `build --pull` re-resolves floating tags on every deploy —
# ghcr.io/astral-sh/uv:latest demonstrably moved during the 2026-08-01 deploy.
# Digests below are the ones running in production as of 2026-08-07.
# Bump deliberately: change the digest, deploy, watch the health check.

# Stage 1: Build frontend assets
FROM docker.io/oven/bun:1@sha256:e10577f0db68676a7024391c6e5cb4b879ebd17188ab750cf10024a6d700e5c4 AS frontend-builder

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
FROM docker.io/python:3.13-slim@sha256:6771159cd4fa5d9bba1258caf0b82e6b73458c694d178ad97c5e925c2d0e1a91

ENV PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/usr/local

WORKDIR /mantis

# Connect to other container via postgres client
RUN apt-get update && \
    apt-get install -y --no-install-recommends postgresql-client && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv@sha256:cf4eedcaa81655197f625739489effcbe71b61ceb1506f332c3facae5deceded /uv /bin/uv

# Install dependencies (uv sync with system Python)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application and install project
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY run.py entrypoint.sh gunicorn.conf.py ./
COPY --from=frontend-builder /build/app/static/build/ ./app/static/build/

RUN uv sync --frozen --no-dev && \
    chmod +x entrypoint.sh

ENV FLASK_APP=run.py
EXPOSE 5000

ENTRYPOINT ["./entrypoint.sh"]
