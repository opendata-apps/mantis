# Stage 1: Build frontend assets
FROM docker.io/oven/bun:1 AS frontend-builder

WORKDIR /build

COPY package.json bun.lock ./
RUN bun install --frozen-lockfile

COPY app/static/js/ ./app/static/js/
COPY app/static/css/ ./app/static/css/
COPY app/templates/ ./app/templates/
COPY tailwind.config.js vite.config.js postcss.config.js ./

RUN bun run build


# Stage 2: Python application
FROM docker.io/python:3.13-slim

WORKDIR /app

# Copy uv binary directly (no pip install needed)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY pyproject.toml uv.lock ./
RUN uv pip install --system .

COPY app/ ./app/
COPY migrations/ ./migrations/
COPY run.py entrypoint.sh ./
COPY --from=frontend-builder /build/app/static/build/ ./app/static/build/

RUN chmod +x entrypoint.sh

ENV FLASK_APP=run.py
EXPOSE 5000

ENTRYPOINT ["./entrypoint.sh"]
