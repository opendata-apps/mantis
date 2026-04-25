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

# Explicit stop+rm avoids podman-compose --force-recreate failing when
# leftover dev containers (e.g. infrastructure_vite_1) claim a dependency.
# A SHA check after `up` is the safety net: it fails loudly if the running
# container did not pick up the freshly-built image.
# Pull latest, rebuild web, verify health. Never touches the DB volume.
@prod-deploy:
    git pull --ff-only
    {{ compose }} build --pull web
    -podman stop -t 10 infrastructure_web_1
    -podman rm -f infrastructure_web_1
    {{ compose }} up -d --no-deps web
    podman image prune -f --filter "dangling=true"
    bash -c 'run=$(podman inspect infrastructure_web_1 --format "{{{{.Image}}"); tag=$(podman image inspect localhost/infrastructure_web:latest --format "{{{{.Id}}"); [ "$run" = "$tag" ] || { echo "✗ image SHA mismatch: running=$run latest=$tag"; exit 1; }; echo "✓ image SHA matches: $run"'
    curl -fsS --retry 30 --retry-delay 2 --retry-all-errors http://localhost:5000/health && echo "✔ deploy ok"
