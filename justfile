set dotenv-load := false

# Only production needs the file list. Development needs nothing: compose.override.yaml
# loads by itself, so the dev stack is `cd infrastructure && podman-compose up`.
# Spelled out here rather than taken from COMPOSE_FILE so these recipes behave the
# same whatever the shell they run in.
#
# -p is not redundant with the `name:` in compose.prod.yaml. podman-compose 1.5
# reports the last file's name from `config` but addresses containers under the
# first file's name at runtime, so without -p every recipe here talks to the
# development project and finds nothing.
compose := "podman-compose -p infrastructure -f infrastructure/compose.yaml -f infrastructure/compose.prod.yaml"

# The same directory compose.prod.yaml bind-mounts. Written from both sides:
# pg_dump lands here from the host, the yearly archives from inside the
# container. Outside the checkout, which prod-deploy runs `git pull` in.
backup_dir := "/home/mantis/data/backups/postgres"

# Not `set default-list := true`, which needs just 1.52; the server runs 1.50.
@_default:
    just --list

# A container's log starts when the container does, and prod-deploy recreates
# it, so this cannot see past the last deploy. journald keeps the request log
# across container swaps:
#     journalctl _UID=$(id -u mantis) --since '3 days ago'
# Show production web logs
[group('prod')]
@prod-logs *ARGS="--tail 100":
    {{ compose }} logs {{ ARGS }} web

# Open a psql shell on the production database
[group('prod')]
@prod-db *ARGS:
    {{ compose }} exec db psql -U mantis_user -d mantis_tracker {{ ARGS }}

# Confirmed because it takes the live site down.
# Stop production
[group('prod')]
[confirm("Stop production? [y/N]")]
@prod-down *ARGS:
    {{ compose }} down {{ ARGS }}

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
    dir="{{ backup_dir }}"
    mkdir -p "$dir"
    part="$dir/.db_$d.dump.partial"
    {{ compose }} exec -T db pg_dump -U mantis_user -Fc mantis_tracker > "$part"
    {{ compose }} exec -T db pg_dumpall -U mantis_user --globals-only --no-role-passwords \
        > "$dir/globals_$d.sql"
    {{ compose }} exec -T db sh -c \
        'cat > /tmp/verify.dump && pg_restore --list /tmp/verify.dump > /dev/null && rm -f /tmp/verify.dump' \
        < "$part"
    mv "$part" "$dir/db_$d.dump"
    echo "✔ $dir/db_$d.dump ($(du -h "$dir/db_$d.dump" | cut -f1))"
    find "$dir" -name 'db_*.dump' -mtime +14 -delete
    find "$dir" -name 'globals_*.sql' -mtime +14 -delete

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
# request proves the app is up *and* that it is the code we just built.
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
        {{ compose }} logs --tail 40 web 2>&1
        exit 1
    fi
    echo "✔ deploy ok — $sha"
    podman image prune -f --filter "dangling=true"

# Does not run migrations — schema changes that landed with the bad
# deploy stay applied; the previous image must still be compatible.
# If it is not, restore the newest {{ backup_dir }}/db_*.dump instead.
# /health will read "unknown" afterwards: the :previous tag records no commit,
# and inventing one would be worse than admitting we don't know.
# Roll back web to the :previous image tag. Use after a failed deploy.
[group('prod')]
@prod-rollback:
    podman tag localhost/infrastructure_web:previous localhost/infrastructure_web:latest
    {{ compose }} up -d --force-recreate --no-deps web
    curl -fsS --retry 30 --retry-delay 2 --retry-all-errors http://localhost:5000/health && echo "✔ rollback ok"
