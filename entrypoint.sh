#!/bin/bash
set -e

# Run migrations
flask db upgrade

# Seed database (idempotent)
if [ "$FLASK_DEBUG" = "1" ]; then
    flask seed --demo
else
    flask seed
fi

echo "Starting: $*"

# The image's CMD, or a command passed in its place.
exec "$@"
