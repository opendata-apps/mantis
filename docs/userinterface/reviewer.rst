Reviewer-Oberfläche
===================

Geltungsbereich
---------------

Dieses Kapitel beschreibt den Reviewer-Workflow für Prüfung, Korrektur und
Freigabe von Meldungen.

Relevante Routen:

- ``/reviewer``: Einstieg mit vorhandener Reviewer-Session
- ``/reviewer/<usrid>``: URL-basierter Einstieg für Reviewer
- ``/modal/<id>`` und ``/modal/<tab>/<id>``: Detaildialog je Meldung
- ``/admin/export/xlsx/<value>``: XLSX-Export

Zugriff und Sitzung
-------------------

- Zugriff ist auf Nutzer mit Rolle ``9`` beschränkt
- ``/reviewer/<usrid>`` setzt bei gültigem Reviewer die Session
- ``/reviewer`` ohne Session liefert ``401``
- Standardparameter beim Einstieg: ``statusInput=offen``,
  ``sort_order=id_desc``

Arbeitsoberfläche
-----------------

Die Seite besteht aus Filter-/Suchleiste, Meldungskarten und Paginierung.
Jede Karte enthält Bild, Ortsmetadaten, Datumsangaben und Schnellaktionen.

Filter, Suche und Sortierung
----------------------------

Statusfilter ``statusInput``:

- ``offen``
- ``bearbeitet`` (Status "angenommen")
- ``unklar``
- ``informiert``
- ``geloescht``
- ``all``

Typfilter ``typeInput``:

- ``maennlich``, ``weiblich``, ``oothek``, ``Nymphe``, ``andere``,
  ``nicht_bestimmt``, ``all``

Datumsfilter:

- ``dateType=fund`` für Funddatum
- ``dateType=meld`` für Meldedatum
- ``dateFrom`` und ``dateTo`` im Format ``dd.mm.yyyy``

Suche:

- ``search_type=id``: exakte Suche über Meldungs-ID
- ``search_type=full_text``: PostgreSQL-FTS über ``search_vector``
  mit ``websearch_to_tsquery('german', ...)``
- unterstützte Syntax in der UI: Phrasen in Anführungszeichen,
  ``OR``, Ausschluss mit ``-`` und Gruppierung mit Klammern

Sortierung und Pagination:

- ``sort_order=id_asc`` oder ``sort_order=id_desc``
- Default ``per_page=21``, Maximum ``100``

Statusmodell und Aktionen
-------------------------

Workflow-Status:

- ``OPEN``: offen
- ``APPR``: angenommen
- ``DEL``: gelöscht

Zusatz-Flags:

- ``UNKL``: unklar
- ``INFO``: informiert

Kartenaktionen:

- :guilabel:`Annehmen`: schaltet zwischen ``OPEN`` und ``APPR``
- :guilabel:`Unklar` / :guilabel:`Informiert`: toggelt Flags (nur bei offenen Meldungen)
- :guilabel:`Löschen` / :guilabel:`Wiederherstellen`: setzt ``DEL`` bzw. ``OPEN``
- :guilabel:`Bearbeiten`: öffnet Modal mit Detailansicht

Bei Annahme wird ``dat_bear`` gesetzt; beim Zurücksetzen auf offen wird
``dat_bear`` geleert. Optionaler E-Mail-Versand an Melder erfolgt nur bei
Konfiguration ``REVIEWERMAIL=true`` und vorhandener E-Mail-Adresse.

Modal-Workflow
--------------

Tab :guilabel:`General Information`:

- Zähler für Männchen/Weibchen/Nymphe/Oothek/Andere/Anzahl
- Quelldaten (``fo_quelle``, ``amt``, ``mtb``)
- Melderkommentar und Reviewerkommentar
- Nutzerkontext mit User-ID, E-Mail und Anzahl bisheriger Meldungen

Tab :guilabel:`Position auf der Karte`:

- Bearbeitung von Koordinaten
- Marker-Neupositionierung auf Leaflet-Karte
- Reverse-Geocoding und Adressupdate
- automatische Neuberechnung von ``amt`` und ``mtb`` nach Koordinatenänderung

Bearbeitungsmodus:

- Offene Meldungen sind direkt editierbar
- Angenommene Meldungen starten read-only und wechseln über
  :guilabel:`Bearbeiten` in den Edit-Modus

Export
------

Folgende Exporttypen stehen als XLSX bereit:

- ``all``: alle Meldungen
- ``accepted``: angenommene Meldungen
- ``non_accepted``: offene Meldungen
- ``searched``: aktuelles Such-/Filterergebnis

``searched`` übernimmt aktive Filterparameter
(``statusInput``, ``typeInput``, ``q``, ``search_type``,
``dateFrom``, ``dateTo``, ``dateType``).
