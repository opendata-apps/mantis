#!/bin/bash
set -e

echo "Warte auf die Datenbank..."
while ! nc -z db 5432; do
  sleep 1
done
echo "Datenbank ist bereit."

# Initialisiere die DB (nur wenn keine Alembic Umgebung existiert)
if [ ! -d "migrations" ]; then
  flask db init
fi

flask db migrate -m "Initialisierung" || true
flask db upgrade

flask create_all_data_view

# Seed database (idempotent)
# Development mode gets demo data, production gets base only
if [ "$FLASK_ENV" = "development" ]; then
    flask seed --demo
else
    flask seed
fi

echo "Starte Flask..."
exec flask run --host=0.0.0.0 --port=5000
