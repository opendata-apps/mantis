set dotenv-load := false

compose := "podman-compose -f infrastructure/podman-compose.prod.yml"
compose_dev := compose + " -f infrastructure/podman-compose.dev.yml"

@_default:
    just --list

# Build dev containers
@build *ARGS:
    {{ compose_dev }} build {{ ARGS }}

# Start dev environment (hot-reload + Vite)
@up *ARGS:
    {{ compose_dev }} up {{ ARGS }}

# Stop dev environment
@down *ARGS:
    {{ compose_dev }} down {{ ARGS }}

# Show container logs
@logs *ARGS:
    {{ compose_dev }} logs {{ ARGS }}

# Open bash shell in web container
@shell:
    {{ compose_dev }} exec web bash

# Open psql shell in db container
@db:
    {{ compose_dev }} exec db psql -U mantis_user -d mantis_tracker

# Run database migrations
@migrate *ARGS:
    {{ compose_dev }} exec web flask db upgrade {{ ARGS }}

# Seed base data
@seed *ARGS:
    {{ compose_dev }} exec web flask seed {{ ARGS }}

# Fetch fresh AGS data from official WFS services
@seed-ags:
    {{ compose_dev }} exec web flask seed-ags

# Start production (detached)
@prod *ARGS="-d":
    {{ compose }} up {{ ARGS }}

# Stop production
@prod-down *ARGS:
    {{ compose }} down {{ ARGS }}

# Pull latest, rebuild web, verify health. Never touches the DB volume.
@prod-deploy:
    git pull --ff-only
    {{ compose }} up -d --build --force-recreate --no-deps web
    curl -fsS --retry 15 --retry-delay 1 --retry-connrefused http://localhost:5000/health && echo "✔ deploy ok"
