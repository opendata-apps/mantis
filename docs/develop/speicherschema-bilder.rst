Bildablage-System
=================
.. index:: Ablage; Bilder
.. index:: Bilder; Ablage

Speicherschema
--------------
- Bilder werden nach dem Funddatum in Ordnern gespeichert.
- Der Dateiname enthält die Stadt, das Meldedatum und die Zeit sowie die Benutzer-ID. Die Datei ist immer im .webp-Format.

::

    datastore
      └──2023
          │
          ├───2023-05-10
          │     Berlin-20230903191152-c3e9af52a535850764f59cff83302792adc0d645.webp
          │
          ├───2023-05-11
          │     Hamburg-20230904121314-836b9c0a3c4d2fa8c4b9f933a6c6aef4b9e0d7f6.webp
          │
          └───2023-05-12
                Muenchen-20230905131516-7a0d6f0b4e8f9fa9d7b8g9a7b6a5c4d3e2f1g0h9.webp

Erklärung:
- Die oberste Ebene des Speicherschemas repräsentiert das Jahr des Fundes (in diesem Fall 2023).
- Innerhalb des Jahrsordners werden die Bilder nach dem genauen Funddatum (Jahr-Monat-Tag) in Unterordnern gespeichert.
- Der Dateiname beginnt mit dem Namen der Stadt, gefolgt von dem Datum und der Uhrzeit der Meldung im Format JahrMonatTagStundeMinuteSekunde.
- Nach dem Datum und der Uhrzeit folgt die Benutzer-ID. Diese ID ist ein eindeutiger Hash-Wert, der den Melder identifiziert.
- Alle Bilder werden im .webp-Format gespeichert, um Speicherplatz zu sparen und schnelle Ladezeiten zu gewährleisten.

Beispiel:
- Im ersten Unterordner ("2023-05-10") befindet sich ein Bild, das in Berlin gefunden wurde. Die Meldung wurde am 3. September 2023 um 19:11:52 Uhr gemacht. Die Benutzer-ID des Melders ist "c3e9af52a535850764f59cff83302792adc0d645".
- Im zweiten Unterordner ("2023-05-11") befindet sich ein Bild, das in Hamburg gefunden wurde. Die Meldung wurde am 4. September 2023 um 12:13:14 Uhr gemacht. Die Benutzer-ID des Melders ist "836b9c0a3c4d2fa8c4b9f933a6c6aef4b9e0d7f6".
- Im dritten Unterordner ("2023-05-12") befindet sich ein Bild, das in München gefunden wurde. Die Meldung wurde am 5. September 2023 um 13:15:16 Uhr gemacht. Die Benutzer-ID des Melders ist "7a0d6f0b4e8f9fa9d7b8g9a7b6a5c4d3e2f1g0h9".
