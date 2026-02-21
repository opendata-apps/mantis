Frontend- und Asset-Pipeline
============================

Quellen und Build-Ziele
-----------------------

- CSS-Quelle: ``app/static/css/theme.css``
- JS-Quellen: ``app/static/js/*.js``
- Build-Ausgabe: ``app/static/build/``
- Vite-Manifest: ``app/static/build/.vite/manifest.json``

Vite-Skripte (``package.json``)
-------------------------------

.. list-table::
   :header-rows: 1

   * - Skript
     - Kommando
     - Zweck
   * - ``dev``
     - ``vite``
     - lokaler Dev-Server
   * - ``build``
     - ``vite build``
     - Produktionsbuild
   * - ``watch``
     - ``vite build --watch``
     - kontinuierlicher Rebuild

Template-Integration
--------------------

Die Flask-Integration liegt in ``app/tools/vite.py``.

Verfügbare Template-Helper:

- ``vite_asset(entry)``
- ``vite_css(entry)``
- ``vite_preload(entry)``
- ``vite_tags(entry)``

In Produktion werden Hash-Dateien aus dem Manifest aufgelöst.
Im Fallback (kein Manifest) werden ungebundelte Assets aus ``app/static`` genutzt.

Laufzeitverhalten lokal
-----------------------

``run.py`` startet beim App-Start automatisch ``bun run watch`` und beendet den
Watcher beim Shutdown. Dadurch reicht lokal ein einzelner Startbefehl:

.. code-block:: bash

   uv run python run.py

Containerbetrieb
----------------

In ``infrastructure/podman-compose.dev.yml`` läuft ein eigener ``vite``-Service
mit ``bunx vite build --watch``.

Wichtige Hinweise
-----------------

- ``app/static/build`` ist Build-Ausgabe und wird nicht manuell bearbeitet.
- Änderungen an Entry-Points in ``app/static/js`` wirken sich auf
  Manifest-Einträge und Template-Imports aus.
- Bei fehlenden Styles/Skripten zuerst prüfen:

  1. ``bun install`` wurde ausgeführt
  2. ``bun run build`` oder Watcher läuft
  3. Manifest unter ``app/static/build/.vite/manifest.json`` existiert
