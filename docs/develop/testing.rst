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
- Benutzer ``mantis_user`` mit ``CREATEDB``-Berechtigung
- Entwicklungsabhängigkeiten: ``uv sync --extra dev``

Die Test-Datenbank ``mantis_tester`` wird automatisch erstellt und nach
Testende gelöscht. Einmalig muss ``CREATEDB`` vergeben werden:

.. code-block:: sql

   ALTER USER mantis_user CREATEDB;

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

1. ``mantis_tester`` wird automatisch erstellt (``sqlalchemy-utils``).
2. App wird mit ``app.test_config.Config`` erstellt.
3. Alembic-Migrationen laufen gegen ``mantis_tester``.
4. Basisdaten, Demo-Meldungen und Materialized View werden aufgebaut.

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
- Die Datenbank wird nach Testende automatisch gelöscht (``DROP DATABASE``).
