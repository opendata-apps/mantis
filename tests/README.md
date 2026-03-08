# Test-Suite

Diese Test-Suite nutzt Pytest mit echter PostgreSQL-Datenbank.

## Voraussetzungen

- laufender PostgreSQL-Server
- Benutzer `mantis_user` mit `CREATEDB`-Berechtigung
- Abhängigkeiten installiert mit `uv sync --extra dev`

Die Test-Datenbank `mantis_tester` wird automatisch erstellt und nach Testende gelöscht.
Einmalig muss `CREATEDB` vergeben werden:

```sql
ALTER USER mantis_user CREATEDB;
```

## Start

```bash
uv run pytest
```

Weitere Läufe:

```bash
uv run pytest -m unit
uv run pytest tests/functional/test_report_submission.py -v
uv run pytest --cov=app --cov-report=term-missing
```

## Struktur

```text
tests/
├── unit/         # kleine, fokussierte Unit-Tests
├── functional/   # Route- und Workflow-Tests
├── database/     # Datenbank- und Modelltests
├── statistics/   # Statistik-/Aggregationslogik
├── tools/        # Hilfsmodul-Tests
├── conftest.py   # zentrale Fixtures und DB-Lifecycle
└── pytest.ini    # Marker und pytest-Optionen
```

## Marker

In `tests/pytest.ini`:

- `unit`
- `web`
- `e2e`
- `api`

## Fixture-Lifecycle (Kurzfassung)

- Session-Scope: Datenbank wird erstellt, Migrationen laufen, Basisdaten werden geladen.
- Function-Scope: Jeder Test läuft in eigener Transaktion mit anschließendem Rollback.
- Teardown: Datenbank wird automatisch gelöscht.

Die Fixture-Implementierung liegt in `tests/conftest.py`.
