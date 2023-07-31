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
-- Vorzugsweise in Einzelschritten

\c mantis_tracker;
begin;
\i /home/ram/disk/pp11/mantis/tests/demodata/beschreibung.sql
\i /home/ram/disk/pp11/mantis/tests/demodata/gen_melder_und_finder.sql
\i /home/ram/disk/pp11/mantis/tests/demodata/import_meldungen.sql
\i /home/ram/disk/pp11/mantis/tests/demodata/fundorte.sql
insert into melduser select id, id , 1 from meldungen;
\i /home/ram/disk/pp11/mantis/tests/demodata/fill-melduser.sql
\i /home/ram/disk/pp11/mantis/tests/demodata/fill-zuordnung.sql

-- \copy plzort(plz, ort, bundesland, landkreis) FROM  WITH (FORMAT csv, DELIMITER ',', HEADER true, ENCODING 'utf-8')

--  Max-Wert für die ID's justieren

SELECT setval('beschreibung_id_seq', (SELECT MAX(id) FROM beschreibung));
SELECT setval('fundorte_id_seq', (SELECT MAX(id) FROM fundorte));
SELECT setval('meldungen_id_seq', (SELECT MAX(id) FROM meldungen));
SELECT setval('melduser_id_seq', (SELECT MAX(id) FROM melduser));
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));



--
-- Alle Daten zusamenführen (CSV-Export)
--

select
  me.id, dat_fund_von, dat_fund_bis, dat_meld, dat_bear,
  anzahl, fo_quelle, art_m, art_w, art_n, art_o, anm_melder, anm_bearbeiter,
  be.beschreibung,
  user_id,  user_name, user_rolle, user_kontakt,
  plz, ort, strasse, land, kreis, amt, mtb, longitude, latitude, ablage


 from melduser mu
  left join meldungen me on mu.id_meldung = me.id
  left join users us on mu.id_user = us.id
  left join fundorte fo on me.fo_zuordnung = fo.id
  left join beschreibung be on fo.beschreibung = be.id;
