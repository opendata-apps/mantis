# -p is required: podman-compose 1.5 takes the project name from the first
# file, so compose.prod.yaml's `name:` alone would address the dev project.
compose := "podman-compose -p infrastructure -f infrastructure/compose.yaml -f infrastructure/compose.prod.yaml"

# Bind-mounted by compose.prod.yaml, outside the checkout prod-deploy pulls into.
backup_dir := "/home/mantis/data/backups/postgres"

# Not `set default-list := true`, which needs just 1.52; the server runs 1.50.
@_default:
    just --list

# Reaches back only to the last deploy; journald keeps older logs (UTC):
#     journalctl _UID=$(id -u mantis) --since '3 days ago'

# Show production web logs
[group('prod')]
@prod-logs *ARGS="--tail 100":
    {{ compose }} logs {{ ARGS }} web

# positional-arguments, not {{ ARGS }}: plain interpolation splits on spaces, so
# `just prod-db -c "SELECT count(*) FROM meldungen;"` would reach sh unquoted.

# Open a psql shell on the production database
[group('prod')]
[positional-arguments]
@prod-db *ARGS:
    {{ compose }} exec db psql -U mantis_user -d mantis_tracker "$@"

# Takes the live site down.

# Stop production
[group('prod')]
[confirm("Stop production? [y/N]")]
@prod-down *ARGS:
    {{ compose }} down {{ ARGS }}

# Roles are a second dump: a single-database dump carries no role definitions,
# so a rebuilt cluster would have no mantis_user.

# Dump the production database (custom format) + roles, verify, rotate at 14d.
[group('prod')]
prod-backup:
    #!/usr/bin/env bash
    set -euo pipefail
    umask 077
    d=$(date +%F_%H-%M)
    dir="{{ backup_dir }}"
    mkdir -p "$dir"
    # Renamed below, after pg_restore accepts it.
    part="$dir/.db_$d.dump.partial"
    # -Fc is compressed and restorable selectively with pg_restore.
    {{ compose }} exec -T db pg_dump -U mantis_user -Fc mantis_tracker > "$part"
    # Without --no-role-passwords, pg_dumpall reads pg_authid and aborts:
    # mantis_user is not a superuser. Role passwords come from the environment
    # on restore.
    {{ compose }} exec -T db pg_dumpall -U mantis_user --globals-only --no-role-passwords \
        > "$dir/globals_$d.sql"
    # pg_restore cannot read an archive from stdin ("could not open input
    # file: -"). Running it here keeps the check off the web container.
    {{ compose }} exec -T db sh -c \
        'umask 077; cat > /tmp/verify.dump && pg_restore --list /tmp/verify.dump > /dev/null && rm -f /tmp/verify.dump' \
        < "$part"
    mv "$part" "$dir/db_$d.dump"
    echo "✔ $dir/db_$d.dump ($(du -h "$dir/db_$d.dump" | cut -f1))"
    find "$dir" -name 'db_*.dump' -mtime +14 -delete
    find "$dir" -name 'globals_*.sql' -mtime +14 -delete

# Runs against the live database while the current container keeps serving.
# prod-deploy applies the same migrations after the swap has removed it.

# Apply pending migrations without swapping the container
[group('prod')]
@prod-migrate:
    # entrypoint.sh upgrades before it execs the command, so the upgrade shows
    # up twice. The second run is a no-op.
    {{ compose }} run --rm -T --no-deps web flask db upgrade

# The new container migrates on boot (entrypoint.sh); a broken migration makes
# it crash-loop. `just prod-migrate` applies migrations beforehand.

# Pull latest, back up, rebuild & swap web, verify the running commit.
[group('prod')]
prod-deploy: prod-backup
    #!/usr/bin/env bash
    set -euo pipefail
    git pull --ff-only
    sha=$(git rev-parse --short HEAD)
    # Before the build, so prod-rollback is a one-liner.
    podman tag localhost/infrastructure_web:latest localhost/infrastructure_web:previous || true
    {{ compose }} build --pull web
    # --no-deps leaves the DB container and its volume out of the swap.
    GIT_SHA=$sha {{ compose }} up -d --force-recreate --no-deps web
    # Captured apart from the version check: in one pipe, pipefail aborts before
    # the log below runs.
    # 25 retries, not 30: /health is rate limited to 30/min and -f retries a 429.
    if ! health=$(curl -fsS --retry 25 --retry-delay 2 --retry-all-errors http://localhost:5000/health); then
        echo "✗ /health never answered — the container is not serving. Last 40 lines:"
        {{ compose }} logs --tail 40 web 2>&1
        exit 1
    fi
    running=$(printf '%s' "$health" \
        | python3 -c 'import json, sys; print(json.load(sys.stdin)["version"])')
    # GIT_SHA is set at run time, so this is the commit the container started on.
    if [ "$running" != "$sha" ]; then
        echo "✗ running $running, expected $sha — roll back with: just prod-rollback"
        {{ compose }} logs --tail 40 web 2>&1
        exit 1
    fi
    echo "✔ deploy ok — $sha"
    # Last, so a failed verification still has both images.
    podman image prune -f --filter "dangling=true"

# Does not downgrade the schema: the previous image must work with it, or
# restore the newest {{ backup_dir }}/db_*.dump. A fully cached build leaves both
# tags on one image id. /health reads "unknown" afterwards.

# Roll back web to the :previous image tag. Use after a failed deploy.
[group('prod')]
@prod-rollback:
    podman tag localhost/infrastructure_web:previous localhost/infrastructure_web:latest
    {{ compose }} up -d --force-recreate --no-deps web
    curl -fsS --retry 30 --retry-delay 2 --retry-all-errors http://localhost:5000/health && echo "✔ rollback ok"
