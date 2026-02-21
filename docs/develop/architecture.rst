Architektur
===========

Systemkontext
-------------

Die Anwendung ist eine Flask-Webapplikation mit PostgreSQL, dateibasierter
Bildablage und einem Vite-Build für statische Assets.

.. code-block:: text

   Browser (Öffentlich / Melder / Reviewer)
              |
              v
      Flask App (Blueprints)
              |
     +--------+---------+
     |                  |
     v                  v
   PostgreSQL       app/datastore (WebP)
   (Meldungen,      YYYY/YYYY-MM-DD/*
   Fundorte, ...)
              ^
              |
   Vite Build (app/static/build + manifest)

Hauptkomponenten
----------------

- ``app/__init__.py``: App-Factory, Extension-Setup, Blueprint-Registrierung,
  Error-Handler, Security-Header, ProxyFix.
- ``app/routes/``: HTTP-Schnittstelle nach Domänen getrennt
  (``main``, ``report``, ``data``, ``statistics``, ``provider``, ``admin``, ``regionen``).
- ``app/database/``: SQLAlchemy-Modelle, Materialized-View-Logik und Seed/Populate-Code.
- ``app/tools/``: Fachliche Hilfsfunktionen (Koordinaten, MTB, Gemeinde, E-Mail, Vite-Helper).
- ``app/templates/`` und ``app/static/``: HTML-Templates, JS/CSS-Quellen, Build-Artefakte.
- ``migrations/``: Alembic-Migrationen für Schema-, Trigger- und Indexänderungen.

HTTP-Flächen und Zuständigkeiten
--------------------------------

- ``main``: öffentliche Inhaltsseiten, Startseite, ``/health``, Sitemap, Robots.
- ``report``: mehrstufiges Meldeformular, HTMX-Teilvalidierungen, Persistierung von Meldung und Bild.
- ``data``: Karten- und Marker-Daten für öffentlich sichtbare, freigegebene Meldungen.
- ``statistics``: Reviewer-geschützte Statistikansichten und Aggregationen.
- ``provider``: Melderansicht eigener Meldungen inkl. Bildauslieferung.
- ``admin``: Reviewer-Oberfläche, Status-/Metadatenpflege, Export, Superuser-Tabellenbearbeitung.
- ``regionen``: SEO-/Landing-Pages aus YAML-Inhalten.

Datenmodell (Kern)
------------------

- ``meldungen`` (``TblMeldungen``): fachlicher Kern einer Meldung inkl. Statusarray.
- ``fundorte`` (``TblFundorte``): Orts- und Ablageinformationen, 1:n zu ``meldungen``.
- ``users`` (``TblUsers``): Melder, Finder, Reviewer.
- ``melduser`` (``TblMeldungUser``): Verknüpfung Meldung zu Melder/Finder.
- ``beschreibung`` (``TblFundortBeschreibung``): Katalog von Fundorttypen.
- ``user_feedback`` (``TblUserFeedback``): Herkunft der Meldung pro User.
- ``all_data_view`` (``TblAllData``): materialisierte Sicht für Admin/Superuser-Abfragen.

Statusmodell
------------

Die Meldungszustände sind als ``statuses``-Array modelliert
(``app/database/report_status.py``):

- Workflow-Zustände (genau einer): ``OPEN``, ``APPR`` oder ``DEL``.
- Zusatzflags: ``INFO`` und ``UNKL``.
- ``DEL`` ist exklusiv.
- ``APPR`` ist exklusiv.
- ``INFO``/``UNKL`` werden mit ``OPEN`` kombiniert.

Kritische Laufzeitflüsse
------------------------

Meldung erfassen
^^^^^^^^^^^^^^^^

1. Client sendet Formulardaten an ``/melden``.
2. Formularvalidierung und Honeypot-Prüfung.
3. Melder/Finder-Nutzer werden gelesen oder erzeugt.
4. Bild wird als WebP unter ``UPLOAD_FOLDER/YYYY/YYYY-MM-DD`` gespeichert.
5. ``fundorte``-, ``meldungen``- und ``melduser``-Datensätze werden transaktional angelegt.
6. Erfolgsantwort liefert Redirect-Ziel auf ``/success``.

Review-Workflow
^^^^^^^^^^^^^^^

1. Reviewer öffnet ``/reviewer``.
2. Filter-/Suchparameter werden serverseitig angewendet.
3. Statuswechsel, Metadatenänderungen und Exporte laufen über Admin-Endpunkte.
4. Materialized View ``all_data_view`` wird bedarfsweise aktualisiert.

Sicherheits- und Betriebsmechanismen
------------------------------------

- CSRF-Schutz global aktiv (Flask-WTF).
- Globales Rate-Limit: ``200/day`` und ``100/hour``.
- Zusätzliche Limits auf relevanten Formular- und HTMX-Endpunkten.
- Security-Header im ``after_request``-Hook.
- ``ProxyFix`` für Betrieb hinter Reverse Proxy.
- ``/health`` führt Datenbankprobe ``SELECT 1`` aus.
- Fehlerpfade liefern HTML oder JSON abhängig vom ``Accept``-Header.

Frontend-Bindung
----------------

- Vite erzeugt Hash-Artefakte und ``manifest.json``.
- ``app/tools/vite.py`` löst Asset-Pfade auf und rendert Script/CSS/Preload-Tags.
- Templates nutzen ``vite_asset`` bzw. ``vite_tags``.

Erweiterungspunkte
------------------

- Neue Route: Blueprint ergänzen und in ``create_app`` registrieren.
- Neues Datenfeld: Modell + Migration + betroffene Formulare/Templates.
- Neue Review-Aktion: Admin-Endpunkt + HTMX-Partial + Status-/Rechteprüfung.
- Neue Statistik: Handler in ``app/routes/statistics.py`` und Template ergänzen.
