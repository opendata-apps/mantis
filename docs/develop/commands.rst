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
     - Basisdaten einspielen (nutzt lokale JSON-Fallback-Datei)
   * - ``uv run flask seed --demo``
     - Basisdaten plus Demo-Meldungen/Bilder einspielen
   * - ``uv run flask seed-ags``
     - Verwaltungsgebiete (AGS) von BKG/Berlin-WFS aktualisieren

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

Container-Workflow
------------------

Der Entwicklungsstack braucht keine Flags: ``compose.override.yaml`` wird
von Compose selbst geladen, sobald man in ``infrastructure/`` steht.

.. code-block:: bash

   cd infrastructure
   podman-compose up --build
   podman-compose down
   podman-compose logs -f web
   podman-compose exec web bash
   podman-compose exec db psql -U mantis_user -d mantis_tracker
   podman-compose exec web flask db upgrade
   podman-compose exec web flask seed
   podman-compose exec web flask seed-ags

Produktion verlangt die zweite Datei ausdrücklich — ohne sie landet man im
Entwicklungsstack:

.. code-block:: bash

   podman-compose -f compose.yaml -f compose.prod.yaml up -d

   # oder einmal pro Sitzung setzen statt an jeden Befehl hängen:
   export COMPOSE_FILE=compose.yaml:compose.prod.yaml

Container-Workflow (just)
-------------------------

``just`` deckt nur ab, was eigene Logik trägt und reproduzierbar sein muss.
Alles andere ist ein gewöhnlicher Compose-Befehl.

.. list-table::
   :header-rows: 1

   * - Befehl
     - Zweck
   * - ``just prod-backup``
     - Dump + Rollen sichern, verifizieren, nach 14 Tagen rotieren
   * - ``just prod-deploy``
     - Sichern, pullen, bauen, Web tauschen, laufenden Commit prüfen
   * - ``just prod-rollback``
     - Web auf das ``:previous``-Image zurücksetzen
   * - ``just prod-down``
     - Produktionsstack stoppen (mit Rückfrage)
