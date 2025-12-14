#!/bin/bash
set -e

# Warten, bis die DB bereit ist
echo "Warte auf die Datenbank..."
while ! nc -z db 5432; do
  sleep 1
done
echo "Datenbank ist bereit."

# Initialisiere die DB (nur wenn migrations-Verzeichnis nicht existiert)
if [ ! -d "migrations" ]; then
  flask db init
fi

flask db migrate -m "Initialisierung"
flask db upgrade
flask create_all_data_view
flask insert_initial_data

# Starte die Anwendung (z. B. über Gunicorn)
exec flask run --host=0.0.0.0

# Alternativ
# exec gunicorn app:app --bind 0.0.0.0:8000,
# je nach Produktionsserver.

