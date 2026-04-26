# Legacy-Dump → aktueller Schema-Stand

Wiederverwendbarer Ablauf, um einen `pg_dump`-SQL-Dump einer älteren
App-Version auf den aktuellen Alembic-HEAD zu heben — **ohne den
Web-Container zu stoppen**. Worker werden eingefroren, Migrationen
laufen direkt aus der Web-Container-Shell.

**Voraussetzungen**
- Postgres → Postgres (kein Engine-Wechsel), PG ≥ 13 für `DROP … FORCE`
- `alembic_version` im Dump ist Vorgänger des aktuellen HEAD
- Daten in der Ziel-DB sind verzichtbar (DB wird gedroppt)
- Container `infrastructure_db_1` und `infrastructure_web_1` laufen

```bash
ssh mantis && work-as-mantis
DUMP=2026-04-26-mantis_tracker.db   # anpassen
```

## Ablauf

### 1) Dump in db-Container kopieren

```bash
podman cp "$DUMP" infrastructure_db_1:/tmp/dump.sql
```

### 2) Web-Worker einfrieren

Keine Request-Verarbeitung, keine Writes, Container bleibt am Leben
(kein Restart, keine Healthcheck-Race-Condition).

```bash
podman exec infrastructure_web_1 pkill -STOP -f gunicorn
```

### 3) Owner/Grant-Statements aus dem Dump strippen

Der Dump referenziert Rollen, die im alpine-Image fehlen
(`mantis_db_user`, `postgres`).

```bash
podman exec infrastructure_db_1 sh -c '
  sed -E "/^ALTER .* OWNER TO/d; /^GRANT /d; /^REVOKE /d;
          /^SET ROLE /d; /^SET SESSION AUTHORIZATION/d" \
      /tmp/dump.sql > /tmp/dump_clean.sql
'
```

### 4) Ziel-DB neu anlegen und Dump einspielen

`WITH (FORCE)` kappt verbliebene Connections automatisch — keine
manuelle `pg_terminate_backend`-Choreografie nötig.

```bash
podman exec infrastructure_db_1 sh -c '
  psql -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 -c \
       "DROP DATABASE IF EXISTS \"$POSTGRES_DB\" WITH (FORCE);"
  psql -U "$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 -c \
       "CREATE DATABASE \"$POSTGRES_DB\" OWNER \"$POSTGRES_USER\";"
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 \
       -f /tmp/dump_clean.sql
'
```

### 5) Legacy-Matviews entfernen

Der neue Alembic-Chain baut eigene auf; alte wären Waisen.

```bash
podman exec infrastructure_db_1 sh -c '
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 <<SQL
DROP MATERIALIZED VIEW IF EXISTS full_text_search CASCADE;
DROP MATERIALIZED VIEW IF EXISTS all_data_view  CASCADE;
SQL
'
```

### 6) Migrationen + Seed aus der Web-Container-Shell

`podman exec` funktioniert auch bei eingefrorenem gunicorn — neue
Prozesse landen außerhalb des Frozen-Trees.

```bash
podman exec -it infrastructure_web_1 bash
```

Drinnen:

```bash
cd /mantis
flask db upgrade   # spielt alle ausstehenden Migrationen ein
flask seed         # legt Matviews und Stamm­daten an
exit
```

### 7) Web-Worker auftauen

```bash
podman exec infrastructure_web_1 pkill -CONT -f gunicorn
```

Healthcheck wird nach ~30 s wieder grün:

```bash
podman ps
```

### 8) Aufräumen

```bash
podman exec infrastructure_db_1 rm -f /tmp/dump.sql /tmp/dump_clean.sql
```

## Verifikation

```bash
podman exec -it infrastructure_db_1 sh -c \
  'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' <<'SQL'
SELECT version_num AS alembic_head FROM alembic_version;
SELECT
  (SELECT COUNT(*) FROM users)         AS users,
  (SELECT COUNT(*) FROM meldungen)     AS meldungen,
  (SELECT COUNT(*) FROM fundorte)      AS fundorte,
  (SELECT COUNT(*) FROM melduser)      AS melduser,
  (SELECT COUNT(*) FROM user_feedback) AS user_feedback;
SELECT statuses, COUNT(*) FROM meldungen GROUP BY 1 ORDER BY 2 DESC;
SELECT
  COUNT(*) FILTER (WHERE search_vector IS NOT NULL) AS sv_ok,
  COUNT(*) FILTER (WHERE search_vector IS NULL)     AS sv_missing
FROM meldungen;
SQL
```

Healthcheck-Endpoint:

```bash
podman exec infrastructure_web_1 sh -c \
  'python -c "import urllib.request; print(urllib.request.urlopen(\"http://localhost:5000/health\").read())"'
```

## Rollback

Der Dump ist das Rollback. Schritte 2–7 erneut ausführen — Schritt 4
droppt die DB, der Ablauf ist also idempotent. Vor riskanten Eingriffen
zusätzlich Snapshot ziehen:

```bash
podman exec infrastructure_db_1 sh -c \
  'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' \
  > "snapshot-$(date +%F).sql"
```

## Stolperfallen

- **Owner-Rollen im Dump fehlen im Image** → Schritt 3 strippt sie weg.
- **Legacy-Matviews** (`full_text_search`, `all_data_view`) blockieren
  den neuen FTS-Chain nicht hart, bleiben aber als Stale-Daten liegen
  → Schritt 5.
- **`DROP DATABASE` ohne `FORCE`** scheitert, solange noch eine
  Connection offen ist. `FORCE` (PG ≥ 13) erledigt das in einem Schritt.
- **`pkill -STOP gunicorn` friert auch den Master ein.** Healthcheck
  schlägt während des Frozen-Fensters fehl — das ist okay, die
  Restart-Policy (`unless-stopped`) reagiert nicht auf Healthcheck-
  Failures, nur auf Container-Exit. Trotzdem nicht stundenlang frieren
  lassen.
- **`podman-compose ps -q SERVICE` ist auf diesem Host kaputt** →
  Container immer beim Namen ansprechen.
