Meldeprozess und Melderansicht
==============================

Geltungsbereich
---------------

Dieses Kapitel dokumentiert den öffentlichen Meldeprozess und die
persönliche Meldungshistorie für Melder.

Relevante Routen:

- ``/melden``: Vier-Schritt-Formular ohne Vorbelegung
- ``/melden/<usrid>``: Formular mit Vorbelegung aus vorhandener User-ID
- ``/success``: Abschlussseite nach erfolgreicher Speicherung
- ``/report/<usrid>`` und ``/sichtungen/<usrid>``: persönliche Historie
- ``/auswertungen``: öffentliche Karte bestätigter Meldungen

Formularablauf (4 Schritte)
---------------------------

1. :guilabel:`Foto & Details`

   - Pflichtfoto hochladen (Drag-and-Drop oder Dateiauswahl)
   - Entwicklungsstadium/Geschlecht auswählen
   - Fundortbeschreibung auswählen
   - optional Freitext (maximal 500 Zeichen)

2. :guilabel:`Wann und Wo? (Ort & Datum)`

   - Funddatum setzen
   - Fundpunkt auf Karte setzen oder Koordinaten manuell eingeben
   - Adressdaten prüfen und bei Bedarf korrigieren

3. :guilabel:`Ihre Kontaktdaten`

   - Vorname und Nachname des Melders (Pflicht)
   - E-Mail optional
   - optional abweichenden Finder erfassen
   - optional Feedbackquelle erfassen (nur falls für den Nutzer noch nicht vorhanden)

4. :guilabel:`Überprüfen & Absenden`

   - Zusammenfassung aller Eingaben
   - Rücksprung in vorherige Schritte möglich
   - endgültiges Absenden per :guilabel:`Absenden`

Validierungsregeln (Server)
---------------------------

- Foto ist Pflicht, max. 12 MB, erlaubte Formate: ``jpg``, ``jpeg``,
  ``png``, ``webp``, ``heic``, ``heif``
- Funddatum ist Pflicht und muss in der Vergangenheit liegen
- Funddatum darf nicht weiter als ca. 5 Jahre zurückliegen
- Breitengrad ist Pflicht und muss im Bereich ``-90`` bis ``90`` liegen
- Längengrad ist Pflicht und muss im Bereich ``-180`` bis ``180`` liegen
- Stadt/Ort und Bundesland sind Pflicht
- Melder-Vorname und Melder-Nachname sind Pflicht
- Finderdaten sind konsistent zu erfassen (Vor- und Nachname zusammen)
- Honeypot-Feld muss leer sein

Client-Unterstützung
--------------------

- Bild wird im Browser zu WebP aufbereitet und als Vorschau angezeigt
- EXIF-Daten können Funddatum und Koordinaten vorbelegen
- Reverse-Geocoding ergänzt Adressfelder auf Basis der Koordinaten
- Schrittvalidierung läuft über HTMX-Endpunkte:

  - ``POST /melden/validate-step``
  - ``POST /melden/toggle-finder``
  - ``POST /melden/feedback-detail``
  - ``POST /melden/review``

Rate Limits
-----------

- ``POST /melden``: ``10 pro Stunde`` und ``3 pro Minute``
- ``POST /melden/validate-step``: ``60 pro Minute``
- ``POST /melden/review``: ``30 pro Minute``

Speicherung nach erfolgreichem Submit
-------------------------------------

- Foto wird als ``.webp`` unter
  ``<UPLOAD_FOLDER>/<Jahr>/<YYYY-MM-DD>/<stadt>-<timestamp>-<usrid>.webp`` gespeichert
- Melder wird angelegt oder über ``<usrid>`` wiederverwendet
- optionaler Finder wird als eigener Nutzer (Rolle ``2``) angelegt
- Standortdatensatz (``fundorte``) wird angelegt
- Meldungsdatensatz (``meldungen``) wird angelegt
- Verknüpfung Melder/Finder/Meldung (``melduser``) wird angelegt

Abschluss und Folgeschritte
---------------------------

- Erfolgreiches Submit liefert JSON mit ``redirect_url`` auf ``/success``
- Bei vorhandenem ``usrid`` zeigt ``/success`` den Einstieg in
  ``/sichtungen/<usrid>``
- Persönliche Historie zeigt vorhandene Meldungen inklusive Bild, Datum,
  Koordinaten und Bearbeitungsstatus

.. warning::

   Der Link ``/sichtungen/<usrid>`` ist ein Zugriffsschlüssel auf die
   persönliche Historie und sollte nicht weitergegeben werden.

Öffentliche Karte (Auswertungen)
--------------------------------

- Es werden nur angenommene Meldungen angezeigt
- Es werden nur Meldungen ab ``MIN_MAP_YEAR`` berücksichtigt
- Markerpositionen werden aus Datenschutzgründen leicht verfälscht
