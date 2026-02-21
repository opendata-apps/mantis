Tests
=====

Überblick
---------

Die Test-Suite basiert auf Pytest und verwendet eine echte PostgreSQL-Datenbank.
Die Fixtures in ``tests/conftest.py`` migrieren und befüllen ``mantis_tester``
automatisch.

Voraussetzungen
---------------

- laufender PostgreSQL-Server
- Datenbank ``mantis_tester``
- Benutzer ``mantis_user`` mit Zugriff auf ``mantis_tester``
- Entwicklungsabhängigkeiten: ``uv sync --extra dev``

Testläufe
---------

.. code-block:: bash

   uv run pytest
   uv run pytest -m unit
   uv run pytest --cov=app --cov-report=term-missing

Marker und Scope
----------------

In ``tests/pytest.ini`` sind folgende Marker definiert:

- ``unit``
- ``web``
- ``e2e``
- ``api``

Tests befinden sich in:

- ``tests/unit``
- ``tests/functional``
- ``tests/database``
- ``tests/statistics``
- ``tests/tools``

Fixture-Lebenszyklus
--------------------

Session-Scope:

1. App wird mit ``app.test_config.Config`` erstellt.
2. Alembic-Migrationen laufen gegen ``mantis_tester``.
3. Basisdaten, Demo-Meldungen und Materialized View werden aufgebaut.

Function-Scope:

1. Pro Test wird eine eigene DB-Transaktion gestartet.
2. Nach dem Test erfolgt Rollback.
3. Tests bleiben isoliert, auch bei Schreiboperationen.

Wichtige Fixtures
-----------------

- ``app``: Flask-App mit Testkonfiguration
- ``client``: Flask-Testclient
- ``session``: transaktionale DB-Session pro Testfunktion
- ``session_with_user`` / ``authenticated_client``: Session mit gesetztem ``user_id``

Hinweise
--------

- Standardoptionen sind ``-x -l`` (Abbruch beim ersten Fehler, lokaler Kontext).
- Tests laufen gegen ``mantis_tester``, nicht gegen ``mantis_tracker``.
