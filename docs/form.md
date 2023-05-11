## Mantisbeschreibung

* Nutzereingaben

  1. Bild der Mantisse
  2. Geschlechtszuordnung
  3. Bildbeschreibung
* Flask App

  1. Bild Metadaten durchsuchen* Datum

  * GPS Daten
  * Dateiformat
  * Dateigröße
  * Dateipfad

  1. Fundort Quelle = immer Fund
  2. evtl. AI Zuordnung

## Fundort

* Nutzereingabe (Unterschiedlich je nachdem was in den Metadaten des Bildes vorhanden ist)
  1. Koordinaten
  2. PLZ
  3. ORT
  4. Straße
  5. Land
  6. Kreis
  7. Fundort Beschreibung
* Flask App


## Meldungsinformationen

* Nutzereingaben
  1. Name
  2. Vorname
  3. Funddatum (weiß ich nicht mehr -> ? / Vielleicht aus Metadaten lesen)
  4. Kontakt (Email/Telefonnummer)
  5. Soll Rückmeldung bei Bearbeitung kommen?
* Flask App
  1. user ID
  2. user role
  3. einsenddatum
  4. meldung ID
  5. bearbeitungsdatum




classReportMantisReligiosaForm(FlaskForm):

    1. Mantisbeschreibung

    Bild

    Geschlecht

    Bildbeschreibung

    Aus den Bild Metadaten GPS Datei infos etc auslesen

    Fundort Quelle (gefunden exkusrion literatur) ist immer Fund (F)

    2. Fundort

    Nutzereingabe (Unterschiedlich je nachdem was in den Metadaten des Bildes vorhanden ist)1. Koordinaten

2. PLZ
3. ORT
4. Straße
5. Land
6. Kreis
7. Fundort Beschreibung

   Meldungsinformationen

Nutzereingaben

1. Name
2. Vorname
3. Funddatum (weiß ich nicht mehr ->?/ Vielleicht aus Metadaten lesen)
4. Kontakt (Email/Telefonnummer)
5. Soll Rückmeldung bei Bearbeitung kommen?

  Datenbank generiert dann

1. user ID
2. user role
3. einsenddatum
4. meldung ID
5. bearbeitungsdatum
