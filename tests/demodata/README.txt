-- Einalig: Datenbank löschen und/oder neu anlegen
-- DROP DATABASE IF EXISTS mantis_tracker;
-- CREATE DATABASE mantis_tracker;

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
-- cd tests/demodata
-- python fill-db.py > demodata.sql
-- in der DB:

\c mantis_tracker;

-- Tabelle mit Beschreibungen füllen
\i /pfad/zur/instanz/von/mantis/tests/demodata/beschreibung.sql
\i /pfad/zur/instanz/von/mantis/tests/demodata/demodaten.sql

-- Einen Reviewer definieren

insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
           values (1, '9999','Reviewer R.', '9', 'reviewer@example.de');
	   
--  Max-Wert für die ID's justieren (falls notwendig)

SELECT setval('beschreibung_id_seq', (SELECT MAX(id) FROM beschreibung));
SELECT setval('fundorte_id_seq', (SELECT MAX(id) FROM fundorte));
SELECT setval('meldungen_id_seq', (SELECT MAX(id) FROM meldungen));
SELECT setval('melduser_id_seq', (SELECT MAX(id) FROM melduser));
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));

--
-- Ausgabe aller Daten (CSV-Export)
--

select
  me.id, deleted, dat_fund_von, dat_fund_bis, dat_meld, dat_bear,
  fo_quelle, tiere, art_m, art_w, art_n, art_o, art_f, anm_melder, anm_bearbeiter,
  be.beschreibung,
  user_id,  user_name, user_rolle, user_kontakt,
  plz, ort, strasse, land, kreis, amt, mtb, longitude, latitude, ablage


 from melduser mu
  left join meldungen me on mu.id_meldung = me.id
  left join users us on mu.id_user = us.id
  left join fundorte fo on me.fo_zuordnung = fo.id
  left join beschreibung be on fo.beschreibung = be.id;

