Befehlsreferenz
===============

Diese Seite ist die zentrale Kommandoübersicht für Entwicklung, Test und Betrieb.

Python- und Node-Abhängigkeiten
-------------------------------

.. code-block:: bash

   uv sync --extra dev
   uv sync --extra docs
   bun install

Lokaler Start (ohne Container)
------------------------------

.. code-block:: bash

   uv run python run.py

Hinweis: ``run.py`` startet Flask und zusätzlich ``bun run watch``.

Flask-CLI
---------

.. list-table::
   :header-rows: 1

   * - Befehl
     - Zweck
   * - ``uv run flask db upgrade``
     - Migrationen auf aktuellen Stand bringen
   * - ``uv run flask db migrate -m "..."``
     - neue Alembic-Migration erzeugen
   * - ``uv run flask create_all_data_view``
     - Materialized View ``all_data_view`` erzeugen
   * - ``uv run flask seed``
     - Basisdaten einspielen
   * - ``uv run flask seed --demo``
     - Basisdaten plus Demo-Meldungen/Bilder einspielen

Qualitätssicherung
------------------

.. code-block:: bash

   uv run ruff check .
   uv run pyright
   uv run pytest
   uv run pytest -m unit
   uv run pytest --cov=app --cov-report=term-missing

Sphinx-Dokumentation
--------------------

.. code-block:: bash

   make -C docs html
   uv run sphinx-build -W --keep-going -b html docs /tmp/mantis-docs-build

Vite-Build
----------

.. code-block:: bash

   bun run build
   bun run watch

Container-Workflow (just)
-------------------------

``justfile`` kapselt den Compose-Aufruf:

.. list-table::
   :header-rows: 1

   * - Befehl
     - Zweck
   * - ``just up --build``
     - Entwicklungsstack starten
   * - ``just down``
     - Entwicklungsstack stoppen
   * - ``just logs``
     - Container-Logs anzeigen
   * - ``just shell``
     - Shell im Web-Container öffnen
   * - ``just db``
     - ``psql`` im DB-Container öffnen
   * - ``just migrate``
     - Migrationen im Web-Container ausführen
   * - ``just seed``
     - Seed-Befehl im Web-Container ausführen
   * - ``just prod --build``
     - Produktionsstack starten
   * - ``just prod-down``
     - Produktionsstack stoppen

Direkter Compose-Aufruf
-----------------------

.. code-block:: bash

   podman-compose -f infrastructure/podman-compose.prod.yml -f infrastructure/podman-compose.dev.yml up --build
   podman-compose -f infrastructure/podman-compose.prod.yml -f infrastructure/podman-compose.dev.yml down
