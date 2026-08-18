set dotenv-load := false

# Neither line carries -p: the project name travels with the files, so anyone
# invoking podman-compose by hand gets the same isolation these recipes do.
# Both stacks share one base, and running them under one project name would let
# a dev recipe drive the *live* containers — with FLASK_DEBUG=1, which makes
# entrypoint.sh seed demo reports into the production database.
# https://github.com/compose-spec/compose-spec/blob/main/04-version-and-name.md
compose := "podman-compose -f infrastructure/compose.yaml -f infrastructure/compose.prod.yaml"
compose_dev := "podman-compose -f infrastructure/compose.yaml -f infrastructure/compose.override.yaml"

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
    d=$(date +%F_%H-%M)
    mkdir -p backups/postgres
    part="backups/postgres/.db_$d.dump.partial"
    {{ compose }} exec -T db pg_dump -U mantis_user -Fc mantis_tracker > "$part"
    {{ compose }} exec -T db pg_dumpall -U mantis_user --globals-only --no-role-passwords \
        > "backups/postgres/globals_$d.sql"
    {{ compose }} exec -T db sh -c \
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
# Tags :previous before the build so `just prod-rollback` is a one-liner.
# `--no-deps` keeps the DB container and its volume out of the swap.
# The health response carries the commit the container was started with, so one
# request proves the app is up *and* that it is the code we just built — which
# is what the old image-id comparison was reaching for the long way round.
# Prune runs last so a failed verification still has both images to fall back on.
# Pull latest, back up, rebuild & swap web, verify the running commit.
[group('prod')]
prod-deploy: prod-backup
    #!/usr/bin/env bash
    set -euo pipefail
    git pull --ff-only
    sha=$(git rev-parse --short HEAD)
    podman tag localhost/infrastructure_web:latest localhost/infrastructure_web:previous || true
    {{ compose }} build --pull web
    GIT_SHA=$sha {{ compose }} up -d --force-recreate --no-deps web
    running=$(curl -fsS --retry 30 --retry-delay 2 --retry-all-errors http://localhost:5000/health \
        | python3 -c 'import json, sys; print(json.load(sys.stdin)["version"])')
    if [ "$running" != "$sha" ]; then
        echo "✗ running $running, expected $sha — roll back with: just prod-rollback"
        {{ compose }} logs --tail 40 web
        exit 1
    fi
    echo "✔ deploy ok — $sha"
    podman image prune -f --filter "dangling=true"

# Does not run migrations — schema changes that landed with the bad
# deploy stay applied; the previous image must still be compatible.
# If it is not, restore the newest backups/postgres/db_*.dump instead.
# /health will read "unknown" afterwards: the :previous tag records no commit,
# and inventing one would be worse than admitting we don't know.
# Roll back web to the :previous image tag. Use after a failed deploy.
[group('prod')]
@prod-rollback:
    podman tag localhost/infrastructure_web:previous localhost/infrastructure_web:latest
    {{ compose }} up -d --force-recreate --no-deps web
    curl -fsS --retry 30 --retry-delay 2 --retry-all-errors http://localhost:5000/health && echo "✔ rollback ok"
