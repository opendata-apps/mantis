FROM python:3.13-slim

WORKDIR /app



# Systemtools für nc
RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

# uv installieren
RUN pip install --no-cache-dir uv

# Abhängigkeiten kopieren & installieren
COPY pyproject.toml uv.lock ./
RUN uv pip install --system .

# Projektdateien kopieren
COPY . .

ENV FLASK_APP=run.py
ENV FLASK_ENV=development
ENV PYTHONPATH=/app

# EntryPoint executable machen
RUN chmod +x /app/entrypoint.sh

ENV FLASK_APP=run.py
ENV FLASK_ENV=development

EXPOSE 5000

ENTRYPOINT ["/app/entrypoint.sh"]

