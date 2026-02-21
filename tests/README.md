# Test-Suite

Diese Test-Suite nutzt Pytest mit echter PostgreSQL-Datenbank.

## Voraussetzungen

- laufender PostgreSQL-Server
- Datenbank `mantis_tester`
- Benutzer `mantis_user` mit Zugriff auf `mantis_tester`
- Abhängigkeiten installiert mit `uv sync --extra dev`

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

- Session-Scope: App wird erstellt, Migrationen laufen, Basisdaten werden geladen.
- Function-Scope: Jeder Test läuft in eigener Transaktion mit anschließendem Rollback.

Die Fixture-Implementierung liegt in `tests/conftest.py`.
