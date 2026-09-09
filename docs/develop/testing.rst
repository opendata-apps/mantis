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
   uv run pytest tests/unit
   uv run pytest --cov=app --cov-report=term-missing
   bun run test

Fixture-Lebenszyklus
--------------------

- ``app`` erstellt pro Test eine Flask-App über die Produktionsfactory.
  ``test_config`` erbt die Produktionskonfiguration über ``tests.test_config.Config``.
  Tests mit abweichender Konfiguration überschreiben diese Fixture vor App-Erstellung.
- ``client`` und ``authenticated_client`` verwenden den normalen Request-Lifecycle.
  Direkte Helpertests aktivieren ``app_ctx`` oder ``request_context`` nur bei Bedarf.
- ``_db`` setzt vor jedem Datenbanktest das Schema zurück, führt Alembic aus
  und lädt Basisdaten, Demo-Meldungen und Materialized View.
- ``session`` verwendet eine eigene Datenbankverbindung. Testdaten für HTTP-
  oder CLI-Aufrufe benötigen ``commit()``. Ein ``flush()`` ist nur innerhalb
  derselben Transaktion sichtbar. Die Anwendung verwendet unverändert ``db.session``.
- Uploads und Backups liegen pro Test unter ``tmp_path``. Unveränderte Favicons
  werden einmal je Testlauf in einem gemeinsamen temporären Verzeichnis erzeugt.
- Migrationstests verwalten ihren Schemaaufbau selbst. Die Datenbank wird
  nach Testende gelöscht. Datenbanktests laufen seriell gegen ``mantis_tester``.

Verifikation und Referenzen
----------------------------

``tests/config/test_application_context.py`` prüft Kontextabbau,
Konfigurationsisolation und temporäre Schreibverzeichnisse.
``tests/config/test_testing_config.py`` vergleicht die geladene App-Konfiguration
mit den Produktionsvorgaben und prüft Cookie-Flags am echten Login.
``tests/config/test_database_isolation.py`` prüft reale Commits, Rollbacks
und den Reset zwischen Tests. Verhalten wird über Antworten und gespeicherte
Ergebnisse geprüft. Netzwerkzugriffe werden an der externen Schnittstelle ersetzt.

Die App-Factory und App pro Test folgen den
`Flask-Testfixtures <https://flask.palletsprojects.com/en/stable/testing/#fixtures>`_
und `Cookiecutter-Flask <https://github.com/cookiecutter-flask/cookiecutter-flask/blob/e5666c23a633b5b6fcb0dc2cfda2441d7f885727/%7B%7Bcookiecutter.app_name%7D%7D/tests/conftest.py>`_.
Cookiecutters globaler Request-Kontext wird nicht übernommen.
Für Kontextgrenzen gilt die aktuelle
`Flask-SQLAlchemy-Dokumentation <https://flask-sqlalchemy.palletsprojects.com/en/stable/contexts/#tests>`_.
PostgreSQL und Alembic bleiben notwendig, weil die Tests auch Trigger,
Volltextsuche und Materialized Views prüfen.

Pytest-Optionen stehen in ``pyproject.toml``. Die Standardoptionen ``-x -l``
brechen beim ersten Fehler ab und zeigen lokale Variablen.
