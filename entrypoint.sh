#!/bin/bash
set -e

# Run migrations
flask db upgrade

# Create materialized view
flask create_all_data_view

# Seed database (idempotent)
if [ "$FLASK_DEBUG" = "1" ]; then
    flask seed --demo
else
    flask seed
fi

echo "Starting application..."

# Gunicorn in production, Flask dev server in development
if [ "$FLASK_DEBUG" = "1" ]; then
    exec flask run --host=0.0.0.0 --port=5000
else
    exec gunicorn run:app --config gunicorn.conf.py
fi
