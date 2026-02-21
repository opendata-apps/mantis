Bildablage
==========

Die Bildablage ist datumssortiert aufgebaut. Standardpfad lokal ist
``app/datastore/``.

Der Basispfad kann über ``UPLOAD_FOLDER`` gesetzt werden und muss ein
absoluter Pfad sein (siehe ``app/config.py``).

Speicherschema
--------------

.. code-block:: text

   app/datastore/
   └── YYYY/
       └── YYYY-MM-DD/
           └── Ort-YYYYMMDDHHMMSS-<user-id>.webp

Regeln
------

- Jahresordner basiert auf ``dat_fund_von``.
- Tagesordner nutzt das Format ``YYYY-MM-DD``.
- Dateiname enthält Ort, Zeitstempel und Benutzer-ID.
- Bilder werden als ``.webp`` gespeichert.

Schreibpfad
-----------

Beim Speichern einer Meldung wird der Pfad in ``report._process_uploaded_image``
gebildet und relativ in ``fundorte.ablage`` persistiert.

Pfadkomponenten:

1. Jahr aus ``sighting_date``
2. Datum aus ``sighting_date``
3. Dateiname ``<city>-<timestamp>-<user-id>.webp``

Konsistenz bei Datumsänderungen
-------------------------------

Wenn ``dat_fund_von`` im Adminbereich geändert wird, wird der Bildpfad
nachgeführt:

- Bilddatei wird in den Zielordner für das neue Datum verschoben
- Dateiname-Zeitstempel wird angepasst
- ``fundorte.ablage`` wird aktualisiert
- leere Quellordner werden bereinigt
- bei Fehlern wird die DB-Änderung zurückgerollt

Die Logik liegt in ``app/routes/admin.py`` (``update_report_image_date`` und Aufruf
aus ``update_cell``).

Beispiel
--------

.. code-block:: text

   app/datastore/2025/2025-01-19/
   Berlin-20250119123000-a88de66aa7976cb7990af54c16c0fd2c067515f9.webp
