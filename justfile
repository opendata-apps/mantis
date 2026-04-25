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

# Migrations run BEFORE swap so a broken schema fails fast — no downtime.
# Container is found via `compose ps -q web` so the recipe survives
# podman-compose's underscore->hyphen separator change (PR #1241).
# Tags :previous before build so `just prod-rollback` is a one-liner.
# SHA-equality check is belt-and-braces against compose claiming a swap
# it didn't make (the failure mode that bit us with infrastructure_vite_1).
# Never touches the DB volume.
# Pull latest, migrate, rebuild & swap web, verify health.
@prod-deploy:
    git pull --ff-only
    -podman tag localhost/infrastructure_web:latest localhost/infrastructure_web:previous
    {{ compose }} build --pull web
    {{ compose }} run --rm web flask db upgrade
    bash -c 'cid=$({{ compose }} ps -q web); if [ -n "$cid" ]; then podman stop -t 10 "$cid"; podman rm -f "$cid"; fi'
    {{ compose }} up -d --no-deps web
    podman image prune -f --filter "dangling=true" | tail -1
    bash -c 'cid=$({{ compose }} ps -q web); run=$(podman inspect "$cid" --format "{{{{.Image}}"); tag=$(podman image inspect localhost/infrastructure_web:latest --format "{{{{.Id}}"); [ "$run" = "$tag" ] || { echo "✗ image SHA mismatch: running=$run latest=$tag"; exit 1; }; echo "✓ image SHA matches: $run"'
    curl -fsS --retry 30 --retry-delay 2 --retry-all-errors http://localhost:5000/health && echo "✔ deploy ok"

# Does not run migrations — schema changes that landed with the bad
# deploy stay applied; the previous image must still be compatible.
# Roll back web to the :previous image tag. Use after a failed deploy.
@prod-rollback:
    podman tag localhost/infrastructure_web:previous localhost/infrastructure_web:latest
    bash -c 'cid=$({{ compose }} ps -q web); if [ -n "$cid" ]; then podman stop -t 10 "$cid"; podman rm -f "$cid"; fi'
    {{ compose }} up -d --no-deps web
    curl -fsS --retry 30 --retry-delay 2 --retry-all-errors http://localhost:5000/health && echo "✔ rollback ok"
