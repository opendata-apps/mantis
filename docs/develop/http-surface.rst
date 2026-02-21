HTTP-Schnittstelle
==================

Überblick nach Blueprints
-------------------------

``main`` (öffentlich)
^^^^^^^^^^^^^^^^^^^^^

- ``/`` und ``/start``: Startseite
- ``/health``: DB-Healthcheck
- ``/faq``, ``/impressum``, ``/lizenz``, ``/datenschutz``
- ``/mantis-religiosa``, ``/bestimmung``
- ``/sitemap.xml``, ``/robots.txt``, ``/favicon.ico``
- ``/galerie``: nur mit ``login_required``

``report`` (öffentlich, rate-limited)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- ``/melden`` und ``/melden/<usrid>`` (GET/POST): Hauptformular
- ``/success``: Abschlussseite
- ``/melden/validate-step`` (POST): HTMX-Stepvalidierung
- ``/melden/toggle-finder`` (POST): HTMX Finder-Abschnitt
- ``/melden/feedback-detail`` (POST): HTMX Feedback-Detail
- ``/melden/review`` (POST): HTMX Review-Partial

``data`` (öffentlich)
^^^^^^^^^^^^^^^^^^^^^

- ``/auswertungen``: Kartenansicht
- ``/get_marker_data/<report_id>``: Marker-Detaildaten

``statistics`` (Reviewer)
^^^^^^^^^^^^^^^^^^^^^^^^^

- ``/statistik`` (GET/POST): zentrale Statistikansicht, ``@reviewer_required``
- ``/statistik/ags`` (GET): AGS-Autocomplete

``provider`` (Melder)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- ``/report/<usrid>`` und ``/sichtungen/<usrid>``: Melderansicht
- ``/images/<filename>``: Bildauslieferung aus ``UPLOAD_FOLDER``

``admin`` (Reviewer)
^^^^^^^^^^^^^^^^^^^^

Einstieg:

- ``/reviewer`` und ``/reviewer/<usrid>`` (Session-/URL-basierte Reviewer-Authentifizierung)

Hauptaktionen:

- Status/Flags: ``/toggle_approve_sighting/<id>``, ``/toggle_flag/<id>``
- Löschlogik: ``/delete_sighting/<id>``, ``/undelete_sighting/<id>``
- Metadaten: ``/change_mantis_meta_data/<id>``, ``/change_mantis_count/<id>``
- Geo/Adresse: ``/update_coordinates/<id>``, ``/update_address/<id>``
- Modals: ``/modal/<id>``, ``/modal/<tab>/<id>``
- Export: ``/admin/export/xlsx/<value>``
- Superuser: ``/alldata``, ``/admin/get_table_data/<table_name>``, ``/admin/update_cell``

Alle oben genannten Admin-Endpunkte (außer ``/reviewer``) sind mit
``@reviewer_required`` geschützt.

``regionen`` (öffentlich)
^^^^^^^^^^^^^^^^^^^^^^^^^

- ``/gottesanbeterin-in-<slug>/``: Landing-Pages aus YAML-Inhalten

Auth- und Antwortverhalten
--------------------------

- Reviewer-Schutz: ``reviewer_required`` (``app/tools/check_reviewer.py``)
- Session-basierter Login für Melderansichten: ``session["user_id"]``
- JSON/HTML-Antworten werden zentral über ``wants_json_response()`` differenziert
  (Error-Handler in ``app/__init__.py``)
