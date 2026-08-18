set dotenv-load := false

# Both stacks are the same compose file plus an override, so without distinct
# project names they resolve to one project (podman-compose derives it from the
# `infrastructure` directory) and a dev recipe run on the server would drive the
# *live* containers — where the dev override sets FLASK_DEBUG=1, which makes
# entrypoint.sh seed demo reports into the production database. Project names are
# the isolation mechanism the spec defines for running the same files twice on
# one host: https://github.com/compose-spec/compose-spec/blob/main/04-version-and-name.md
#
# Prod keeps its implicit `infrastructure` name on purpose. Renaming it resolves
# to a new, empty `mantis_data` volume — an empty database.
compose := "podman-compose -f infrastructure/podman-compose.prod.yml"
compose_dev := "podman-compose -p mantis_dev -f infrastructure/podman-compose.prod.yml -f infrastructure/podman-compose.dev.yml"

# Not `set default-list := true`, which needs just 1.52; the server runs 1.50.
@_default:
    just --list

# Build dev containers
[group('dev')]
@dev-build *ARGS:
    {{ compose_dev }} build {{ ARGS }}

# Start dev environment (hot-reload + Vite)
[group('dev')]
@dev-up *ARGS:
    {{ compose_dev }} up {{ ARGS }}

# Stop dev environment
[group('dev')]
@dev-down *ARGS:
    {{ compose_dev }} down {{ ARGS }}

# Keep the `2>&1`: podman-compose writes container output to both streams —
# gunicorn's access log to stdout, the Flask logger and Postgres to stderr — so
# piping into grep matches nothing while the lines sit on screen (issue #178).
# Show dev container logs
[group('dev')]
@dev-logs *ARGS:
    {{ compose_dev }} logs {{ ARGS }} 2>&1

# Open bash shell in dev web container
[group('dev')]
@dev-shell:
    {{ compose_dev }} exec web bash

# Open psql shell in dev db container
[group('dev')]
@dev-db:
    {{ compose_dev }} exec db psql -U mantis_user -d mantis_tracker

# Run database migrations (dev)
[group('dev')]
@dev-migrate *ARGS:
    {{ compose_dev }} exec web flask db upgrade {{ ARGS }}

# Seed base data (dev)
[group('dev')]
@dev-seed *ARGS:
    {{ compose_dev }} exec web flask seed {{ ARGS }}

# Fetch fresh AGS data from official WFS services (dev)
[group('dev')]
@dev-seed-ags:
    {{ compose_dev }} exec web flask seed-ags

# Start production (detached)
[group('prod')]
@prod *ARGS="-d":
    {{ compose }} up {{ ARGS }}

# Confirmed because it takes the live site down and reads like the dev recipe.
# Stop production
[group('prod')]
[confirm("Stop production? [y/N]")]
@prod-down *ARGS:
    {{ compose }} down {{ ARGS }}

# `-f` is the compose file before the subcommand and --follow after it, which is
# what broke the hand-written command in issue #178. Going through the recipe
# puts the file in front, so `just prod-logs -f` follows as it reads.
# See dev-logs for why the `2>&1` has to stay.
#
# A container's log starts when the container does and prod-deploy recreates it,
# so this cannot reach past the last deploy. journald keeps the full history
# across container swaps:
#     sudo journalctl _UID=$(id -u mantis) --since '3 days ago'
# Not a recipe because the service account cannot read the journal — run it from
# an admin account.
# Show production web logs (only since the running container started)
[group('prod')]
@prod-logs *ARGS="--tail 100":
    {{ compose }} logs {{ ARGS }} web 2>&1

# Open bash shell in the production web container
[group('prod')]
@prod-shell:
    {{ compose }} exec web bash

# Open psql shell in the production db container
[group('prod')]
@prod-db:
    {{ compose }} exec db psql -U mantis_user -d mantis_tracker

# pg_dump -Fc (custom format) is compressed by default and restorable
# selectively with pg_restore; plain SQL piped through gzip is neither.
# Globals are a second dump on purpose: a single-database dump carries no role
# definitions, so restoring into a rebuilt cluster would have no mantis_user.
# --no-role-passwords is required, not cosmetic: without it pg_dumpall reads
# pg_authid, which a non-superuser role cannot, and the dump aborts. Role
# passwords come from the environment on restore anyway.
# Verification runs inside the db container because pg_restore cannot read an
# archive from stdin ("could not open input file: -"), and doing it there keeps
# the backup independent of the web container being up.
# The dump lands on a .partial name and is renamed only after it verifies — a
# half-written archive that looks like a backup is worse than no backup.
# This exists because prod-rollback swaps the image but never downgrades
# schema — a migration that applies cleanly and is wrong has no other undo.
# Dump the production database (custom format) + roles, verify, rotate at 14d.
[group('prod')]
prod-backup:
    #!/usr/bin/env bash
    set -euo pipefail
    cid=$(podman inspect infrastructure_db_1 -f '{{{{.Id}}' 2>/dev/null \
       || podman inspect infrastructure-db-1 -f '{{{{.Id}}' 2>/dev/null)
    d=$(date +%F_%H-%M)
    mkdir -p backups/postgres
    part="backups/postgres/.db_$d.dump.partial"
    podman exec "$cid" pg_dump -U mantis_user -Fc mantis_tracker > "$part"
    podman exec "$cid" pg_dumpall -U mantis_user --globals-only --no-role-passwords \
        > "backups/postgres/globals_$d.sql"
    podman exec -i "$cid" sh -c \
        'cat > /tmp/verify.dump && pg_restore --list /tmp/verify.dump > /dev/null && rm -f /tmp/verify.dump' \
        < "$part"
    mv "$part" "backups/postgres/db_$d.dump"
    echo "✔ backups/postgres/db_$d.dump ($(du -h "backups/postgres/db_$d.dump" | cut -f1))"
    find backups/postgres -name 'db_*.dump' -mtime +14 -delete
    find backups/postgres -name 'globals_*.sql' -mtime +14 -delete

# Migrations are run by entrypoint.sh on container start (`flask db upgrade`),
# so a schema-changing commit will be applied automatically when the new
# container boots. Trade-off: a broken migration causes startup to fail and
# `restart: unless-stopped` will loop until you `just prod-rollback`. We
# don't pre-flight migrations because entrypoint.sh has no `exec "$@"` —
# `compose run --rm web flask db upgrade` would be ignored and run the full
# entrypoint (incl. gunicorn), deadlocking the deploy.
# Container lookup tries `infrastructure_web_1` then `infrastructure-web-1`
# so the recipe survives podman-compose's eventual underscore->hyphen
# separator change (PR #1241). podman-compose's `ps -q SERVICE` doesn't
# accept service args in this version — direct `podman inspect` is the
# robust path.
# Tags :previous before build so `just prod-rollback` is a one-liner.
# SHA-equality check is belt-and-braces against compose claiming a swap
# it didn't make (the failure mode that bit us with infrastructure_vite_1).
# Prune runs after verification so a failed check still has both images.
# `--no-deps` keeps the DB container and its volume out of the swap.
# GIT_SHA is inline rather than a just variable: just evaluates its variables
# at startup, which is before the `git pull` above, so a variable would stamp
# the commit we were on before the deploy.
# Pull latest, back up, rebuild & swap web, verify health.
[group('prod')]
@prod-deploy: prod-backup
    git pull --ff-only
    -podman tag localhost/infrastructure_web:latest localhost/infrastructure_web:previous
    {{ compose }} build --pull web
    bash -c 'cid=$(podman inspect infrastructure_web_1 -f "{{{{.Id}}" 2>/dev/null || podman inspect infrastructure-web-1 -f "{{{{.Id}}" 2>/dev/null || true); if [ -n "$cid" ]; then podman stop -t 10 "$cid"; podman rm -f "$cid"; fi'
    GIT_SHA=$(git rev-parse --short HEAD) {{ compose }} up -d --no-deps web
    bash -c 'cid=$(podman inspect infrastructure_web_1 -f "{{{{.Id}}" 2>/dev/null || podman inspect infrastructure-web-1 -f "{{{{.Id}}" 2>/dev/null); run=$(podman inspect "$cid" --format "{{{{.Image}}"); tag=$(podman image inspect localhost/infrastructure_web:latest --format "{{{{.Id}}"); [ "$run" = "$tag" ] || { echo "✗ image SHA mismatch: running=$run latest=$tag"; exit 1; }; echo "✓ image SHA matches: $run"'
    bash -c 'curl -fsS --retry 30 --retry-delay 2 --retry-all-errors http://localhost:5000/health && echo "✔ deploy ok" || { echo "✗ health check failed — roll back with: just prod-rollback"; podman logs --tail 40 infrastructure_web_1 2>/dev/null || true; exit 1; }'
    podman image prune -f --filter "dangling=true" | tail -1

# Does not run migrations — schema changes that landed with the bad
# deploy stay applied; the previous image must still be compatible.
# If it is not, restore the newest backups/postgres/db_*.dump instead.
# Roll back web to the :previous image tag. Use after a failed deploy.
[group('prod')]
@prod-rollback:
    podman tag localhost/infrastructure_web:previous localhost/infrastructure_web:latest
    bash -c 'cid=$(podman inspect infrastructure_web_1 -f "{{{{.Id}}" 2>/dev/null || podman inspect infrastructure-web-1 -f "{{{{.Id}}" 2>/dev/null || true); if [ -n "$cid" ]; then podman stop -t 10 "$cid"; podman rm -f "$cid"; fi'
    {{ compose }} up -d --no-deps web
    curl -fsS --retry 30 --retry-delay 2 --retry-all-errors http://localhost:5000/health && echo "✔ rollback ok"
