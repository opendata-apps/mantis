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
uv run pytest tests/unit
uv run pytest tests/functional/test_report_submission.py -v
uv run pytest --cov=app --cov-report=term-missing
bun run test
```

Die [Testkonventionen](../docs/develop/testing.rst) beschreiben App-, Datenbank-
und Dateisystem-Isolation sowie die Referenzen zu Flask und Cookiecutter-Flask.
Pytest-Optionen stehen in `pyproject.toml`.
