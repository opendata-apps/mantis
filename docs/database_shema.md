# 🗃️ Mantis Tracker - Database Schema

The Mantis Tracker application uses the following database tables to store information about mantis sightings and related data.

## 🌍 TblFundorte

TblFundorte stores information about the locations where mantis sightings have occurred.

| Column       | Type         | Description                           |
| ------------ | ------------ | ------------------------------------- |
| id           | Integer      | Primary key                           |
| plz          | Integer      | Postal code                           |
| ort          | Integer      | City                                  |
| strasse      | String(255)  | Street                                |
| land         | String(255)  | Country                               |
| kreis        | Integer      | District                              |
| beschreibung | Integer      | Foreign key to TblFundortBeschreibung |
| longitude    | VARCHAR(15)  | Longitude                             |
| latitude     | VARCHAR(15)  | Latitude                              |
| ablage       | VARCHAR(255) | Storage location                      |

## 📝 TblMeldungen

TblMeldungen stores information about individual mantis sightings.

| Column       | Type        | Description                         |
| ------------ | ----------- | ----------------------------------- |
| id           | Integer     | Primary key                         |
| dat_fund     | Date        | Date of the sighting                |
| dat_meld     | Date        | Date of the sighting report         |
| dat_bear     | Date        | Date of processing the sighting     |
| anzahl       | Integer     | Number of mantises sighted          |
| fo_zuordung  | Integer     | Foreign key to TblFundorte          |
| fo_quelle    | String(1)   | Source of sighting                  |
| fo_kategorie | String(1)   | Category of sighting                |
| anmerkung    | String(500) | Additional notes about the sighting |

## 📝 TblMeldungUser

TblMeldungUser links mantis sightings to the users who reported them.

| Column     | Type    | Description                 |
| ---------- | ------- | --------------------------- |
| id         | Integer | Primary key                 |
| id_meldung | Integer | Foreign key to TblMeldungen |
| id_user    | Integer | Foreign key to TblUsers     |

## 🦗 TblTiere

TblTiere stores information about the different species of mantis.

| Column | Type    | Description |
| ------ | ------- | ----------- |
| id     | Integer | Primary key |
| art    | Integer | Species     |

## 🗺️ TblFundortBeschreibung

TblFundortBeschreibung stores descriptions of the locations where mantis sightings have occurred.

| Column       | Type       | Description             |
| ------------ | ---------- | ----------------------- |
| id           | Integer    | Primary key             |
| beschreibung | String(45) | Description of location |

## 🧑‍💼 TblUsers

TblUsers stores information about users who report mantis sightings.

| Column       | Type       | Description              |
| ------------ | ---------- | ------------------------ |
| id           | Integer    | Primary key              |
| user_id      | String(40) | User ID                  |
| user_name    | String(45) | User name                |
| user_rolle   | String(1)  | User role                |
| user_kontakt | String(45) | User contact information |
