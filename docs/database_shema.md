# 🗃️ Mantis Tracker - Database Schema

Mantis Tracker is an application that allows users to report and view mantis sightings on an interactive map. To store the data related to mantis sightings, the application uses a database that contains several tables.

## 🌍 TblFundorte

The TblFundorte table stores information about the locations where mantis sightings have occurred. This information includes the postal code, city, street, country, district, and location description of the sighting. Each location is given a unique identifier (id) and its longitude and latitude are also recorded.

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

The TblMeldungen table stores information about individual mantis sightings. This information includes the date of the sighting, the date the sighting was reported, and the date the sighting was processed. The number of mantises sighted, the source of the sighting, the category of the sighting, and any additional notes are also recorded. Each sighting is given a unique identifier (id) and is linked to the TblFundorte table through a foreign key (fo_zuordung).

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

The TblMeldungUser table links mantis sightings to the users who reported them. Each row in this table represents a connection between a mantis sighting and a user. Each connection is given a unique identifier (id) and is linked to the TblMeldungen and TblUsers tables through foreign keys (id_meldung and id_user, respectively).

| Column     | Type    | Description                 |
| ---------- | ------- | --------------------------- |
| id         | Integer | Primary key                 |
| id_meldung | Integer | Foreign key to TblMeldungen |
| id_user    | Integer | Foreign key to TblUsers     |

## 🦗 TblTiere

The TblTiere table stores information about the different species of mantis. Each species is given a unique identifier (id) and a species code (art).

| Column | Type    | Description |
| ------ | ------- | ----------- |
| id     | Integer | Primary key |
| art    | Integer | Species     |

## 🗺️ TblFundortBeschreibung

The TblFundortBeschreibung table stores descriptions of the locations where mantis sightings have occurred. Each location description is given a unique identifier (id) and a description of the location.

| Column       | Type       | Description             |
| ------------ | ---------- | ----------------------- |
| id           | Integer    | Primary key             |
| beschreibung | String(45) | Description of location |

## 🧑‍💼 TblUsers

The TblUsers table stores information about the users who report mantis sightings. Each user is given a unique identifier (id) and a user ID (user_id), user name (user_name), user role (user_rolle), and user contact information (user_kontakt) are recorded.

By using these tables, the Mantis Tracker application can store and retrieve information about mantis sightings and the users who report them, making it possible to visualize this data on a map and analyze it in various ways.

| Column       | Type       | Description              |
| ------------ | ---------- | ------------------------ |
| id           | Integer    | Primary key              |
| user_id      | String(40) | User ID                  |
| user_name    | String(45) | User name                |
| user_rolle   | String(1)  | User role                |
| user_kontakt | String(45) | User contact information |
