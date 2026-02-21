Installation und lokales Setup
==============================

Diese Seite beschreibt die minimalen Setup-Schritte.
Die vollständigen Kommandos stehen unter ``develop/commands``.

Lokales Setup (ohne Container)
------------------------------

Voraussetzungen
^^^^^^^^^^^^^^^

- Python 3.13+
- ``uv``
- ``bun``
- PostgreSQL 16+

Projekt initialisieren
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   cp .env.example .env
   uv sync --extra dev
   bun install

Lokale Datenbanken anlegen
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: sql

   CREATE USER mantis_user WITH PASSWORD 'mantis';
   CREATE DATABASE mantis_tracker OWNER mantis_user;
   CREATE DATABASE mantis_tester OWNER mantis_user;

Schema und Basisdaten laden
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   uv run flask db upgrade
   uv run flask create_all_data_view
   uv run flask seed
   # optional:
   uv run flask seed --demo

Anwendung starten
^^^^^^^^^^^^^^^^^

.. code-block:: bash

   uv run python run.py

Server-URL: ``http://localhost:5000``.

Container-Setup (Alternative)
-----------------------------

Voraussetzungen:

- Podman oder Docker mit Compose
- ``just``

Start/Stopp:

.. code-block:: bash

   just up --build
   just down

Dokumentation lokal bauen
-------------------------

.. code-block:: bash

   uv sync --extra docs
   make -C docs html

Weiterführende Seiten
---------------------

- ``develop/commands``: komplette Befehlsreferenz
- ``develop/configuration``: Umgebungsvariablen und Profile
- ``develop/architecture``: Systemaufbau und Laufzeitflüsse
