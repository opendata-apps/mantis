-- Einalig: Datenbank löschen und/oder neu anlegen
-- DROP DATABASE IF EXISTS mantis_tracker;
--create database mantis_tracker;

-- in Flask Alembic vorbereiten:
-- migrations-Ordner löschen
-- Aus der README.md die drei Kommandos für die
-- Initalisierung ausführen
-- Alle Tabellen werden neu angelegt
-- 
-- flask db init
-- flask db migrate -m "Initialisierung aller Relationen"
-- flask db upgrade
-- nun der Import aller Demodaten

\c mantis_tracker;
begin;
\i beschreibung.sql
\i gen_melder_und_finder.sql
\i import_meldungen.sql
\i fundorte.sql
--\copy plzort(plz, ort, bundesland, landkreis) FROM  WITH (FORMAT csv, DELIMITER ',', HEADER true, ENCODING 'utf-8')
