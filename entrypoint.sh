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

echo "Starting: $*"

# The image's CMD, or a command passed in its place.
exec "$@"
