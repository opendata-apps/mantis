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

if [ "$LOAD_DEMO_DATA" = "True" ]; then
    if [ ! -f /app/.demo_loaded ]; then
        echo "xx Demodaten werden geladen..."
        flask insert_initial_data
        touch /app/.demo_loaded
    else
        echo "Demodaten wurden bereits geladen – überspringe."
    fi
fi

echo "Starte Flask..."
exec flask run --host=0.0.0.0 --port=5000
