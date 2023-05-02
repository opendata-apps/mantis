# 🗃️ Mantis Tracker - Database Schema

The Mantis Tracker application uses the following database tables to store information about mantis sightings and related data.

## 🌍 TblFundorte

TblFundorte stores information about the locations where mantis sightings have occurred.

| Column       | Type          | Description               |
|--------------|---------------|---------------------------|
| id           | Integer       | Primary key               |
| plz          | Integer       | Postal code               |
| ort          | Integer       | City                      |
| strasse      | String(255)   | Street                    |
| land         | String(255)   | Country                   |
| kreis        | Integer       | District                  |
| beschreibung | String(255)   | Location description      |
| longitude    | VARCHAR(255)  | Longitude                 |
| latitude     | VARCHAR(255)  | Latitude                  |

## 🦗 Mantis

Mantis stores information about individual mantis sightings.

| Column    | Type        | Description                   |
|-----------|-------------|-------------------------------|
| id        | Integer     | Primary key                   |
| latitude  | Float       | Latitude of the sighting      |
| longitude | Float       | Longitude of the sighting     |
| photo_url | String(255) | URL of the mantis photo       |

## 🐾 TblTiere

TblTiere stores information about the different species of mantis.

| Column | Type    | Description     |
|--------|---------|-----------------|
| id     | Integer | Primary key     |
| art    | Integer | Species         |

These tables form the core structure of the Mantis Tracker database, enabling users to report and view mantis sightings on an interactive map.
