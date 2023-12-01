-- admin-Roolen
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (1, '2bcdff3c622d71e280b017d77236497a56cf1f0c ','Berger D.', '9', 'Dirk.Berger@rathaus.potsdam.de');
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (2, '1b9294c08d1c989d4f5a22b060a38d32690266bf','Krüger B.', '9', 'bkrg@bkprivat.de');
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (3, '17d31973137f148369e7862b439bc8f29bf12d0c','Keller M.', '9', 'post@manfred-keller.de');
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (4, 'dc5fb2870f1ad32d5cc80bfc64ff49c3741ce0be','M.Hanke J.', '9', 'maxjac.sky@gmail.com');
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (5, 'd9194afa151fdb93013c4696155fef7967ef6533','', '9', '');
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (6, '77af8b7d6e9f2adc13f8de2550d6e76dab1a217e','', '9', '');
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (7, 'b170e581a269ba886b8f7c544a6f8fabc894878c','', '9', '');
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (8, '532390ae5db6c0940caadf9d9577c7ccd6c3dbd4','Kohlhaußen L.', '9', 'kohli.leon@gmail.com');
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (9, '75f7c447fff33acd6f0fedc1087d97950f334c54','Koppatz P.', '9', 'peter@koppatz.com');
			  
-- Datensätze

--  10
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (10,  '04467582f71ed3912ac8ae6c3cc8f4768cf95d8b','A. Hofmann.', '1', 'hofmann-ariane@gmx.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (10, 14959, 'Trebbin OT Kleinbeuthen','Hortus Terrigenus', 'Brandenburg','Teltow-Fläming',99,'52,258174','13,193184','2023/2023-01-19/Trebbin_OT_Kleinbeuthen-20230727105947-bc1671f6017fb9bfc966864ef9b56be86c531f63.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (10, '2023-01-19',NULL, '2023-01-19', '', '2023-02-16',  'F', 'F', '0', 0, 0, 0, 1, 10,'FO siehe 20230626 Kleinbeuthen (Koordinaten am 26.6.2023 geliefert) 
Fundortbeschreibung Melder: Ablageort auf 1,50 m im Spalt einer Totholzstele, welche als Nisthabitat von Xylocopa violacea genutzt wird. Ausrichtung Süd.
Alter Ablageordner: 2023/20230119 Trebbin OT Kleinbeuthen');
insert into melduser values (10,10,10);

--  11
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (11,  '6276060da28a756c90484621f1d4a6151059d928','H. Bonnowitz.', '1', 'h.bonnowitz@t-online.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (11, 14959, 'Trebbin OT Christinendorf','Im Strumpf 11', 'Brandenburg','Teltow-Fläming',99,'52,211374','13,281649','2023/2023-01-23/Trebbin_OT_Christinendorf-20230727123913-6276060da28a756c90484621f1d4a6151059d928.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (11, '2022-09-16',NULL, '2023-01-23', '', '2023-02-16',  'F', 'F', '1', 0, 1, 0, 0, 11,' 
Fundortbeschreibung Melder: Hoftor
Alter Ablageordner: 2023/20230123 Trebbin OT Christinendorf');
insert into melduser values (11,11,11);
--  13
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (13,  '89bed0e249cd53bc05a5fd83820e27e22a89d213','M. Schostek.', '1', 'nurpost@gmx.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (13, 15517, 'Fürstenwalde/Spree','Luchweg', 'Brandenburg','Oder-Spree',99,'52,354694','14,020111','2023/2023-02-07/Furstenwalde_Spree-20230727123914-89bed0e249cd53bc05a5fd83820e27e22a89d213.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (13, '2022-08-24',NULL, '2023-02-07', '', '2023-04-13',  'F', 'F', '1', 1, 0, 0, 0, 13,'Koordinaten geliefert 
Fundortbeschreibung Melder: im Wohnzimmer
Alter Ablageordner: 2023/20230207 Fürstenwalde/Spree');
insert into melduser values (13,13,13);

--  14
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (14,  '7561447b261f168c9d2c9659d8fa946a67bb2cbf','J. Klein.', '1', 'jojoeule@outlook.com');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (14, 14624, 'Dallgow-Döberitz','Seeburg', 'Brandenburg','Havelland',99,'52,513167','13,135222','2023/2023-02-18/Dallgow-Doberitz-20230727123914-7561447b261f168c9d2c9659d8fa946a67bb2cbf.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (14, '2020-09-17',NULL, '2023-02-18', '', '2023-04-13',  'F', 'F', '1', 0, 1, 0, 0, 14,'Koordinaten geliefert 
Fundortbeschreibung Melder: Offennland
Alter Ablageordner: 2023/20230218 Dallgow-Döberitz');
insert into melduser values (14,14,14);

--  15
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (15,  '5c3158fd0962b889c9385caaed74c394cb6b43b6','E. Balzer.', '1', 'erika.balzer@freenetnde');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (15, 01945, 'Ruhland Gemeindeteil Arnsdorf','Guteborner Straße', 'Brandenburg','Oberspreewald-Lausitz',2,'51,430356','13,866661','2023/2023-02-26/Ruhland_Gemeindeteil_Arnsdorf-20230727123916-e562a5c1c17646b3fe317212d6dab708069ea0b7.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (15, '2022-10-13',NULL, '2023-02-26', '', '2023-04-13',  'F', 'F', '1', 0, 1, 0, 0, 15,'Koordinaten in den Bildeigenschaften 
Fundortbeschreibung Melder: im Garten
Alter Ablageordner: 2023/20230226 Ruhland Gemeindeteil Arnsdorf');
insert into melduser values (15,15,15);

--  16
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (16,  'e562a5c1c17646b3fe317212d6dab708069ea0b7','E. Balzer.', '1', 'erika.balzer@freenetnde');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (16, 01945, 'Ruhland Gemeindeteil Arnsdorf','Guteborner Straße', 'Brandenburg','Oberspreewald-Lausitz',2,'51,430383','13,866628','2023/2023-02-26/Ruhland_Gemeindeteil_Arnsdorf-20230727123916-e562a5c1c17646b3fe317212d6dab708069ea0b7.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (16, '2022-10-16',NULL, '2023-02-26', '', '2023-04-13',  'F', 'F', '1', 0, 1, 0, 0, 16,'Koordinaten in den Bildeigenschaften 
Fundortbeschreibung Melder: im Garten
Alter Ablageordner: 2023/20230226 Ruhland Gemeindeteil Arnsdorf');
insert into melduser values (16,16,16);

--  17
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (17,  '7b8d9cdf3bb60b0beec5c41976354df0c1d4cfff','H. Müller.', '1', '');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (17, 01968, 'Senftenberg OT Brieske','Seniorenanlage an der Schwarzen Elster (ASB), Helmut-Just-Straße 32a', 'Brandenburg','Oberspreewald-Lausitz',99,'51,496972','13,967871','2023/2023-02-28/Senftenberg_OT_Brieske-20230727222415-5c1ed8cca95c0dbecbdffbaf70310b77f0938321.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (17, '2021-06-21','2021-09-22', '2023-02-28', '', '2023-07-18',  'F', 'F', '1', 0, 1, 0, 0, 17,'Meldung per Brief, Funddatum: "Sommer 2021" (Bemerkung auf der Rückseite eines der Fotos), Punkt mitten in die Wohnanlage gesetzt 
Fundortbeschreibung Melder: in der Beetanlage vor der Terrasse
Alter Ablageordner: 2023/20230228 Senftenberg OT Brieske');
insert into melduser values (17,17,17);

--  18 Kein Bild
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (18,  'e244b6ceaeb5bcf0ad095b70e37fde332235151e','F. Schlesener.', '1', 'schlesener@web.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (18, 13127, 'Berlin Pankow, Französisch Buchholz','Schulhof Jeanne-Barez-Schule, Hauptstraße 66', 'Berlin','Berlin',99,'52,604356','13,433730','');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (18, '2022-08-22',NULL, '2023-03-04', '', '2023-04-14',  'F', '?', '1', 0, 0, 0, 0, 18,'Punkt für Koordinaten in die Mitte des Schulhofes gesetzt 
Fundortbeschreibung Melder: 
Alter Ablageordner: 2023/20230304 Berlin Pankow, Französisch Buchholz
kein Bild');
insert into melduser values (18,18,18);

--  19
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (19,  'f64e5c33c3aea7cc4bf37f1f9314efa444328856','R. Peth.', '1', 'ruedigerpe@web.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (19, 03222, 'Lübbenau/Spreewald','Rosa-Luxemburg-Straße', 'Brandenburg','Oberspreewald-Lausitz',2,'51,868130','13,941668','2023/2023-03-15/Lubbenau_Spreewald-20230727123917-f64e5c33c3aea7cc4bf37f1f9314efa444328856.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (19, '2022-09-21',NULL, '2023-03-15', '', '2023-04-14',  'F', 'F', '1', 0, 1, 0, 0, 19,'Koordinaten geliefert 
Fundortbeschreibung Melder: im Garten
Alter Ablageordner: 2023/20230315 Lübbenau/Spreewald');
insert into melduser values (19,19,19);

--  20
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (20,  'e5cf0aabe00943fd1b48f517e1745dc6164461cd','J. Zschau.', '1', 'jan.zschau@uni-potsdam.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (20, 14959, 'Trebbin','Thyrower Bahnhofsstraße 65', 'Brandenburg','Teltow-Fläming',99,'52,248657','13,247587','2023/2023-03-18/Trebbin-20230727123921-e5cf0aabe00943fd1b48f517e1745dc6164461cd.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (20, '2022-12-23',NULL, '2023-03-18', '', '2023-04-14',  'F', 'F', '0', 0, 0, 0, 1, 20,'Koordinaten geliefert 
Fundortbeschreibung Melder: an einer Holzkiste
Alter Ablageordner: 2023/20230318 Trebbin');
insert into melduser values (20,20,20);

--  21
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (21,  'feee391d3a0ff808471e252f9dde7b11a9c4e4b8','H. Neddermann & S. M. Soldanski.', '1', 'hauke.neddermann@googlemail.com');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (21, 10827, 'Berlin Schöneberg','Kärntener Straße', 'Berlin','Berlin',99,'52,479256','13,347364','2023/2023-03-19/Berlin-Schoneberg-20230727202836-9823b8dbacef440a908b5a2bd569b217b55178f4.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (21, '2023-03-19',NULL, '2023-03-19', '', '2023-04-14',  'F', 'F', '1', 0, 1, 0, 0, 21,'Koordinaten in den Bildeigenschaften, Totfund 
Fundortbeschreibung Melder: im Zwischenraum der Balkontür im 4. OG eines Schönberger Mietshauses
Alter Ablageordner: 2023/20230319 Berlin Schöneberg');
insert into melduser values (21,21,21);

--  22
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (22,  '3d5c67cc5e2f617ba5b271f54c34e6b00c7e47c9','K. Meier.', '1', 'karin-e.meier@t-online.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (22, 56263, 'Treis-Karden','an einem flachen Stein  am Hang neben einem steilen Pfad zum Zillesberggipfel hinauf', 'Rheinland-Pfalz','Cochem-Zell',99,'50,176501','7,304659','2023/2023-03-20/Treis-Karden-20230727203210-b5a1e521f5b330331d9c86e0e4a7016b9d6f52ee.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (22, '2023-03-17',NULL, '2023-03-20', '', '2023-04-14',  'F', 'F', '0', 0, 0, 0, 1, 22,'Koordinaten geliefert 
Fundortbeschreibung Melder: 
Alter Ablageordner: 2023/20230320 Treis-Karden');
insert into melduser values (22,22,22);

--  23
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (23,  'ff329103907fa33b7b051e5f005d8659d8600c37','M. Kusche.', '1', 'mikusch60@t-online.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (23, 15746, 'Klein Köris','Flugplatz Löpten', 'Brandenburg','Dahme-Spreewald',99,'52,147244','13,698789','2023/2023-03-21/Klein_Koris-20230727123922-ff329103907fa33b7b051e5f005d8659d8600c37.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (23, '2021-09-04',NULL, '2023-03-21', '', '2023-04-14',  'F', 'F', '1', 0, 0, 1, 0, 23,'Koordinaten in den Bildeigenschaften 
Fundortbeschreibung Melder: 
Alter Ablageordner: 2023/20230321 Klein Köris');
insert into melduser values (23,23,23);

--  24
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (24,  '90e2a1ea3af91fc62cea06f8ca3f014f0beae8dd','K. Kutzner.', '1', 'kl.kutzner@t-online.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (24, 14959, 'Trebbin OT Glau','Friedensstadt, auf dem Wege aus den Glauer Bergen herab zur Friedensstadt', 'Brandenburg','Teltow-Fläming',99,'52,240833','13,151111','2023/2023-03-23/Trebbin_OT_Glau-20230727123924-90e2a1ea3af91fc62cea06f8ca3f014f0beae8dd.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (24, '2022-09-25',NULL, '2023-03-23', '', '2023-04-14',  'F', 'F', '1', 0, 1, 0, 0, 24,'Koordinaten in den Bildeigenschaften 
Fundortbeschreibung Melder: im Nacken, Hemdkragen
Alter Ablageordner: 2023/20230323 Trebbin OT Glau');
insert into melduser values (24,24,24);

--  25
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (25,  '443d4d79763c43eb7f28279e982af621c56a361f','L. Baum.', '1', 'LudwigBaum@t-online.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (25, 01968, 'Senftenberg-Sedlitz','Raunoer Straße 7', 'Brandenburg','Oberspreewald-Lausitz',99,'51,550947','14,055400','2023/2023-03-29/Senftenberg-Sedlitz-20230728055017-0a7ad7cbf5af8b43d7ae17edd58a5b94c86ce65e.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (25, '2022-08-13',NULL, '2023-03-29', '', '2023-04-14',  'F', 'F', '1', 0, 0, 1, 0, 25,' 
Fundortbeschreibung Melder: 
Alter Ablageordner: 2023/20230329 Senftenberg-Sedlitz');
insert into melduser values (25,25,25);

--  26
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (26,  '2d5a22f8bae517dec54e861e65f8660ba50e39d8','R. Kluge.', '1', 'kluge-rene@web.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (26, 14552, 'Michendorf','Fichtenallee', 'Brandenburg','Potsdam-Mittelmark',99,'52,330021','13,083815','2023/2023-03-29/Michendorf-20230727123925-2d5a22f8bae517dec54e861e65f8660ba50e39d8.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (26, '2021-09-28',NULL, '2023-03-29', '', '2023-04-14',  'F', 'F', '1', 0, 1, 0, 0, 26,'Koordinaten geliefert 
Fundortbeschreibung Melder: 
Alter Ablageordner: 2023/20230329 Michendorf');
insert into melduser values (26,26,26);

--  27
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (27,  '61c834c7e550b17b4eb7f93a8228a17577dec314','Joachim E..', '1', 'lysmachia333@startmail.com');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (27, 14089, 'Spandau Kladow','Wanderweg', 'Berlin','Berlin',99,'52,458894','13,162384','2023/2023-04-09/Spandau_Kladow-20230727211042-71d80466dc74a59de4c86c7083e1489fbcb6d19b.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (27, '2023-04-09',NULL, '2023-04-09', '', '2023-04-14',  'F', 'F', '0', 0, 0, 0, 1, 27,'Koordinaten geliefert 
Fundortbeschreibung Melder: 
Alter Ablageordner: 2023/20230409 Spandau Kladow');
insert into melduser values (27,27,27);

--  28
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (28,  'b918916fc18ec436e5ef5c3354e1c6469ba7c35e','U. Zuppke.', '1', 'uwe.zuppke@t-omline.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (28, 06925, 'Annaburg','Alte Elster und Rohrbornwiesen', 'Sachsen-Anhalt','Wittenberg',99,'51,748028','13,131653','2023/2023-05-22/Annaburg-20230727123929-b918916fc18ec436e5ef5c3354e1c6469ba7c35e.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (28, '2022-09-05',NULL, '2023-05-22', '', '2023-05-22',  'F', 'F', '1', 1, 0, 0, 0, 28,'Koordinaten geliefert 
Fundortbeschreibung Melder: 
Alter Ablageordner: 2023/20230522 Annaburg');
insert into melduser values (28,28,28);

--  29
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (29,  '51082d59eca75f16bdbefa9b935a12743f088222','F. Brandt.', '1', 'hofmann-ariane@gmx.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (29, 15838, 'Wünsdorf','Im Schilfgrund 9', 'Brandenburg','Teltow-Fläming',99,'52,171408','13,458034','2023/2023-05-27/Wunsdorf-20230727123930-51082d59eca75f16bdbefa9b935a12743f088222.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (29, '2022-05-21',NULL, '2023-05-27', '', '2023-05-30',  'F', 'F', '1', 0, 0, 1, 1, 29,'Bekannte von Ariane, Besuch auf Exkursion 2022, daher Fundort bekannt, Schlupf diverser Larven, nur eine fotografisch belegt 
Fundortbeschreibung Melder: 
Alter Ablageordner: 2023/20230527 Wünsdorf');
insert into melduser values (29,29,29);

--  30
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (30,  '3cf8f79e9bd2d8e992f18f0e3f001b92fea5bd19','E. Georgi.', '1', 'Whatsapp: 0162-9311329');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (30, 99518, 'Großheringen','Wilhelm-Pieck-Platz 6', 'Thüringen','Weimarer Land',99,'51,102381','11,663859','2023/2023-06-02/Groheringen-20230727123930-3cf8f79e9bd2d8e992f18f0e3f001b92fea5bd19.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (30, '2023-05-26',NULL, '2023-06-02', '', '2023-06-06',  'F', 'F', '50', 0, 0, 50, 1, 30,'Meldung vía whatsApp Manfred K., Oothek im Verlauf des Winters ins Haus (Terrarium) geholt, Zimmerschlupf 
Fundortbeschreibung Melder: auf dem Hof
Alter Ablageordner: 2023/20230602 Großheringen');
insert into melduser values (30,30,30);

--  31 es fehlt in der csv 20230603 Berlin Lichtenrade mb (Mücke)/

insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (31,  '1327668568d996f1c5927bdae6aff8cff01c6bea','H. Gerecke.', '1', 'holger.gerecke@googlemail.com ');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (31, 15806, 'Zossen OT Dabendorf','An den Sakazen 9', 'Brandenburg','Teltow-Fläming',99,'52,245192','13,431144','2023/2023-06-06/Zossen_OT_Dabendorf-20230727123932-1327668568d996f1c5927bdae6aff8cff01c6bea.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (31, '2023-06-04',NULL, '2023-06-06', '', '2023-06-06',  'F', 'F', '2', 0, 0, 2, 0, 31,'Koordinaten in den Bildeigenschaften 
Fundortbeschreibung Melder: 
Alter Ablageordner: 2023/20230606 Zossen OT Dabendorf
Es fehlt in der csv 20230603 Berlin Lichtenrade mb (Mücke)/');
insert into melduser values (31,31,31);

--  32
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (32,  '695b32ecf59566b8b13db7e6eda0fa12a630baaa','M. Klenk.', '1', 'boerkle.mk@gmail.com');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (32, 67292, 'Kirchheimbolanden','Dannenfelser Str. 36', 'Rheinland-Pfalz','Donnersbergkreis',99,'49,658985','8,007653','2023/2023-06-07/Kirchheimbolanden-20230727123933-695b32ecf59566b8b13db7e6eda0fa12a630baaa.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (32, '2022-07-25',NULL, '2023-06-07', '', '2023-06-07',  'F', 'F', '1', 1, 0, 0, 0, 32,'Adresse aus dem Internet recherchiert: "Ausbildungszentrum für Pflegefachberufe des Westpfalz-Klinikums, Standort Kirchheimbolanden Dannenfelser Str. 36 67292 Kirchheimbolanden". Durch Melder bestätigt. 
Fundortbeschreibung Melder: Eingangstür einer Pflegeschule
Alter Ablageordner: 2023/20230607 Kirchheimbolanden');
insert into melduser values (32,32,32);

--  33
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (33,  '1cf2c21315ebce96c89d1181f9660f1212aea731','V.N. Sahan.', '1', 'viviennatalie.sahan@gmail.com');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (33, 14193, 'Berlin Grunewald','Dahlemer Feld', 'Berlin','Berlin',99,'52,479060','13,223560','2023/2023-06-13/Berlin_Grunewald-20230727123934-1cf2c21315ebce96c89d1181f9660f1212aea731.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (33, '2023-06-11',NULL, '2023-06-13', '', '2023-06-13',  'F', 'F', '2', 0, 0, 2, 0, 33,'Koordinaten geliefert, ein Tier durch Foto belegt, 2 Tiere gemeldet 
Fundortbeschreibung Melder: 
Alter Ablageordner: 2023/20230613 Berlin Grunewald');
insert into melduser values (33,33,33);

--  34
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (34,  '33c16fb4f2b6b641463c9eff3126138e8a332037','A. Kallasch.', '1', 'a.kallasch4500@gmail.com');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (34, 12623, 'Berlin Mahlsdorf','Landsberger Straße 52c', 'Berlin','Berlin',99,'52,517351','13,631270','2023/2023-06-15/Berlin_Mahlsdorf-20230727123934-33c16fb4f2b6b641463c9eff3126138e8a332037.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (34, '2023-06-15',NULL, '2023-06-15', '', '2023-06-15',  'F', 'F', '1', 0, 0, 1, 0, 34,'Karte mit Adresse geliefert 
Fundortbeschreibung Melder: 
Alter Ablageordner: 2023/20230615 Berlin Mahlsdorf');
insert into melduser values (34,34,34);

--  35
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (35,  '1e11a54dba5a3aa2727ffa924be87476c8385038','S. Gundlach.', '1', 'fischkopp80@gmx.net');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (35, 14949, 'Trebbin OT Kliestow','Zum Akazienhain 35', 'Brandenburg','Teltow-Fläming',99,'52,191360','13,219337','2023/2023-06-15/Trebbin_OT_Kliestow-20230727123935-1e11a54dba5a3aa2727ffa924be87476c8385038.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (35, '2023-06-15',NULL, '2023-06-15', '', '2023-06-15',  'F', 'F', '1', 0, 0, 1, 0, 35,'Mehrfachmelder FO siehe Meldungen "20210821 Trebbin OT Kliestow" & "2021025 Kliestow" 
Fundortbeschreibung Melder: an Hauswand
Alter Ablageordner: 2023/20230615 Trebbin OT Kliestow');
insert into melduser values (35,35,35);

--  36
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (36,  '947a5530109cb0775f2cb63da20254fbcba7407c','J. Deutschmann.', '1', 'janinedeutschmann@gmx.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (36, 15838, 'Am Mellensee OT Rehagen','Rehagener Bahnhofstraße 13', 'Brandenburg','Teltow-Fläming',1,'52,1667485','13,376386','2023/2023-06-16/Am_Mellensee_OT_Rehagen-20230727123935-947a5530109cb0775f2cb63da20254fbcba7407c.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (36, '2023-06-16',NULL, '2023-06-16', '', '2023-06-16',  'F', 'F', '1', 0, 0, 1, 0, 36,'Koordinaten und Adresse geliefert 
Fundortbeschreibung Melder: am Haus, im Schuh
Alter Ablageordner: 2023/20230616 Am Mellensee OT Rehagen');
insert into melduser values (36,36,36);

--  37
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (37,  '30f53d7a5669e298e2ec6755cb6903849f44e7cd','Y. Lopp.', '1', 'yvonne.lopp@web.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (37, 03249, 'Sonnewalde','Breitenau 16a', 'Brandenburg','Elbe-Elster',2,'51,687464','13,725718','2023/2023-06-19/Sonnewalde-20230727212358-cb3b2c26d2d2af0eab3bbf7df8c58dc1fb36055b.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (37, '2023-06-19',NULL, '2023-06-19', '', '2023-06-19',  'F', 'F', '1', 0, 0, 1, 0, 37,'Pool im Garten (auf dem Foto) in Google Maps zu erkennen 
Fundortbeschreibung Melder: im Garten
Alter Ablageordner: 2023/20230619 Sonnewalde');
insert into melduser values (37,37,37);

--  38
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (38,  '2d027cde299a6364d7b0dbb2bd77f16ffb266377','F. Kramer.', '1', 'flkrmr@googlemail.com');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (38, 03249, 'Sonnewalde OT Pahlsdorf','', 'Brandenburg','Elbe-Elster',99,'51,729360','13,673845','2023/2023-06-19/Sonnewalde_OT_Pahlsdorf-20230727123936-2d027cde299a6364d7b0dbb2bd77f16ffb266377.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (38, '2023-06-19',NULL, '2023-06-19', '', '2023-06-19',  'F', 'F', '1', 0, 0, 1, 0, 38,'Koordinaten geliefert 
Fundortbeschreibung Melder: 
Alter Ablageordner: 2023/20230619 Sonnewalde OT Pahlsdorf');
insert into melduser values (38,38,38);
--  39
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (39,  'f8343def03f9110f2b4ee52e6c04a7d5d7d9a27b','L. Szizybalski.', '1', 'laszizyba@yahoo.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (39, 14943, 'Luckenwalde','Theaterstraße 15 a, Grundschule', 'Brandenburg','Teltow-Fläming',99,'52,088379','13,175685','2023/2023-06-23/Luckenwalde-20230727123937-f8343def03f9110f2b4ee52e6c04a7d5d7d9a27b.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (39, '2022-10-11',NULL, '2023-06-23', '', '2023-06-26',  'F', 'F', '1', 0, 1, 0, 0, 39,'Anhand der Bodenfarbe auf dem Hof der Schule, Punkt mittig auf dem Hof gesetzt 
Fundortbeschreibung Melder: 
Alter Ablageordner: 2023/20230623 Luckenwalde');
insert into melduser values (39,39,39);

--  40
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (40,  '43256ab9a3a11ee3846b51b4a405bc1b789b93db','L. Szizybalski.', '1', 'laszizyba@yahoo.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (40, 14959, 'Trebbin OT Blankensee','Zur Nieplitz 16', 'Brandenburg','Teltow-Fläming',99,'52,241872','13,130584','2023/2023-06-23/Trebbin_OT_Blankensee-20230727123937-43256ab9a3a11ee3846b51b4a405bc1b789b93db.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (40, '2023-09-25',NULL, '2023-06-23', '', '2023-06-26',  'F', 'F', '1', 0, 1, 0, 1, 40,'Zaun zur Straße 
Fundortbeschreibung Melder: 
Alter Ablageordner: 2023/20230623 Trebbin OT Blankensee');
insert into melduser values (40,40,40);

--  41
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (41,  'ec7c0433d43e9abfe449abc853360aad1377d213','G. Jordan.', '1', 'gabijazz@icloud.com');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (41, 14822, 'Linthe','Belziger Strasse 13', 'Brandenburg','Potsdam-Mittelmark',3,'52,154288','12,783632','2023/2023-06-24/Linthe-20230727213622-b74d529c429da42c9638c641c76af9ab5a07b755.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (41, '2023-06-24',NULL, '2023-06-24', '', '2023-06-27',  'F', 'F', '1', 0, 0, 1, 0, 41,' 
Fundortbeschreibung Melder: auf der Terrasse
Alter Ablageordner: 2023/20230624 Linthe');
insert into melduser values (41,41,41);

--  42
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (42,  '0d2576cb14317e265ce5e09e56926204f59e564f','M. Sterzel.', '1', 'mandy.huebner@gmx.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (42, 14554, 'Seddin OT Seddin','Hainbuchenstraße 26', 'Brandenburg','Potsdam-Mittelmark',2,'52,268504','13,016042','2023/2023-06-24/Seddin_OT_Seddin-20230727123938-0d2576cb14317e265ce5e09e56926204f59e564f.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (42, '2023-06-24',NULL, '2023-06-24', '', '2023-06-27',  'F', 'F', '1', 0, 0, 1, 0, 42,'FO siehe 20220810 Seddiner See OT Seddin 
Fundortbeschreibung Melder: im Garten
Alter Ablageordner: 2023/20230624 Seddin OT Seddin');
insert into melduser values (42,42,42);

--  43
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (43,  '5e4a9c2d3143e09204ee69f35b2dd924b295c294','M. Woldt.', '1', 'woldtmaria@gmail.com');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (43, 15517, 'Fürstenwalde/Spree','Lindenstraße 97', 'Brandenburg','Oder-Spree',2,'52,357071','14,068292','2023/2023-06-25/Furstenwalde_Spree-20230727123940-5e4a9c2d3143e09204ee69f35b2dd924b295c294.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (43, '2023-06-25',NULL, '2023-06-25', '', '2023-06-27',  'F', 'F', '2', 0, 0, 2, 0, 43,'hat bereits 2022 gemeldet 
Fundortbeschreibung Melder: im Garten
Alter Ablageordner: 2023/20230625 Fürstenwalde/Spree');
insert into melduser values (43,43,43);

--  44
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (44,  'fb8144d979a7e39e251f1a93725ea26bb11f5b4a','A. Hofmann.', '1', 'hofmann-ariane@gmx.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (44, 14959, 'Trebbin OT Kleinbeuthen','Hortus Terrigenus', 'Brandenburg','Teltow-Fläming',2,'52,258174','13,193184','2023/2023-06-26/Trebbin_OT_Kleinbeuthen-20230727123941-fb8144d979a7e39e251f1a93725ea26bb11f5b4a.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (44, '2023-06-15',NULL, '2023-06-26', '', '2023-06-26',  'F', 'S', '20', 0, 0, 20, 1, 44,'Artenkennerin, Mantidenfreundin, Fund der frischen Larvenhäute, siehe auch Meldung, 20230119 Kleinbeuthen, Koordinaten geliefert, mindestens 20 Tiere geschlüpft 
Fundortbeschreibung Melder: im Garten
Alter Ablageordner: 2023/20230626 Trebbin OT Kleinbeuthen');
insert into melduser values (44,44,44);

--  45
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (45,  '53645ce935a8a7222bbbe98bb66e71229ab9bdce','T. Pietsch.', '1', 'torsten.pietsch@lvwa.sachsen-anhalt.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (45, 06132, 'Halle (Saale)','Distelweg 11', 'Sachsen-Anhalt','Saalekreis',99,'51,448151','11,976434','2023/2023-06-27/Halle_Saale-20230727123941-53645ce935a8a7222bbbe98bb66e71229ab9bdce.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (45, '2023-06-25',NULL, '2023-06-27', '', '2023-06-28',  'F', 'S', '1', 0, 0, 1, 0, 45,'noch einmal nachgehakt, Fund durch T. Pietsch (Artenkenner) angesichert, siehe auch 20230628 Halle (Saale) 
Fundortbeschreibung Melder: 
Alter Ablageordner: 2023/20230627 Halle (Saale)');
insert into melduser values (45,45,45);

--  46 kein Bild
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (46,  'aa97d45cfb051bd8a10825a3d0a6817b1e7c20f0','T. Pietsch.', '1', 'torsten.pietsch@lvwa.sachsen-anhalt.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (46, 06132, 'Halle (Saale)','Distelweg 11', 'Sachsen-Anhalt','Saalekreis',99,'51,448151','11,976434','');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (46, '2023-06-27',NULL, '2023-06-28', '','2023-06-28' ,  'F', 'S', '1', 0, 0, 1, 0, 46,'Artenkenner, sicherer Fund, siehe auch 20230627 Halle (Saale) 
Fundortbeschreibung Melder: 
Alter Ablageordner: 2023/20230628 Halle (Saale)
kein Bild');
insert into melduser values (46,46,46);

--  47
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (47,  'cedcc956cd771b188f4dfb97a831ed2a285ba6c1','F. Kramer.', '1', 'flkrmr@googlemail.com>');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (47, 12524, 'Berlin Treptow-Köpenick','Kleeblattstraße', 'Berlin','Berlin',99,'52,407538','13,550909','2023/2023-06-29/Berlin_Treptow-Kopenick-20230727123941-cedcc956cd771b188f4dfb97a831ed2a285ba6c1.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (47, '2023-06-29',NULL, '2023-06-29', '', '2023-06-29',  'F', 'F', '1', 0, 0, 1, 0, 47,'Koordinaten geliefert 
Fundortbeschreibung Melder: 
Alter Ablageordner: 2023/20230629 Berlin Treptow-Köpenick');
insert into melduser values (47,47,47);

--  48
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (48,  'd3ce76e8b1c84a0fedf699a67917a9651211a8fd','W. Köhler.', '1', '01525/2149026');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (48, 03226, 'Vetschau OT Raddusch','Buschmühlenweg 7b', 'Brandenburg','Oberspreewald-Lausitz',3,'51,820303','14,037161','2023/2023-07-18/Vetschau_OT_Radusch20230729203821-6034950c781829306a2425d340418909ffd1a02d.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (48, '2022-10-13','2022-10-17', '2023-06-30', '', '2023-07-18',  'F', 'F', '1', 0, 1, 0, 0, 48,'Meldung per Brief 
Fundortbeschreibung Melder: Hecke an der Hausterrasse
Alter Ablageordner: 2023/20230630 Vetschau OT Raddusch');
insert into melduser values (48,48,48);

--  49
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (49,  'fa8cea01b57609c5ccf48db586f6dc5cc2b4bd6c','Dr. M. Strödicke.', '1', 'm.stroedicke@gmail.com; 0176/66187574');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (49, 03205, 'Calau','Burgplatz 6', 'Brandenburg','Oberspreewald-Lausitz',99,'51,746977','13,946183','2023/2023-07-01/Calau-20230727123942-fa8cea01b57609c5ccf48db586f6dc5cc2b4bd6c.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (49, '2023-07-01',NULL, '2023-07-01', '', NULL ,  'F', 'F', '1', 0, 0, 1, 0, 49,'Adresse und Koordinaten geliefert 
Fundortbeschreibung Melder: Hauseingangstür
Alter Ablageordner: 2023/20230701 Calau');
insert into melduser values (49,49,49);

--  50
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (50,  'a5ff580fe6a8fb51f6e3ea669daf867fb58043bc','T. Westphal.', '1', 'thilobochow79@gmx.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (50, 15838, 'Am Mellensee','Am Kaffeegraben 1', 'Brandenburg','Teltow-Fläming',99,'52,155722','13,350443','2023/2023-07-02/Am_Mellensee-20230727123942-a5ff580fe6a8fb51f6e3ea669daf867fb58043bc.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (50, '2023-07-02',NULL, '2023-07-02', '', '2023-07-05',  'F', 'F', '1', 0, 0, 1, 0, 50,' 
Fundortbeschreibung Melder: 
Alter Ablageordner: 2023/20230702 Am Mellensee');
insert into melduser values (50,50,50);

--  51
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (51,  '103dcbdd58e7b5d01eac0910a32924c893f80586','B. Gottwald.', '1', 'WhatsApp ');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (51, 14548, 'Schwielowsee OT Caputh','', 'Brandenburg','Potsdam-Mittelmark',6,'52,343977','13,015612','2023/2023-07-04/Schwielowsee_OT_Caputh-20230727123944-103dcbdd58e7b5d01eac0910a32924c893f80586.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (51, '2023-07-04',NULL, '2023-07-04', '', '2023-07-05',  'F', 'F', '3', 0, 0, 3, 0, 51,'Koordinaten geliefert 
Fundortbeschreibung Melder: Lichtung/ Trasse, im Fangeimer für Reptilien
Alter Ablageordner: 2023/20230704 Schwielowsee OT Caputh');
insert into melduser values (51,51,51);

--  52
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (52,  '4fb8185ae9042f532e0fcb6beebfe1d6ebe78af4','T. Siedler.', '1', 'tino.siedler@naturundtext.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (52, 14959, 'Trebbin OT Klein Schulzendorf','Trebbiner Straße 74', 'Brandenburg','Teltow-Fläming',99,'52,202750','13,242753','2023/2023-07-04/Trebbin_OT_Klein_Schulzendorf-20230727123945-4fb8185ae9042f532e0fcb6beebfe1d6ebe78af4.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (52, '2023-07-03',NULL, '2023-07-04', '', '2023-07-05',  'F', 'F', '2', 0, 0, 2, 0, 52,'Finder: Nachbarn 
Fundortbeschreibung Melder: Hauswand
Alter Ablageordner: 2023/20230704 Trebbin OT Klein Schulzendorf');
insert into melduser values (52,52,52);

--  53
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (53,  '42186a11773f23862e83a2301dd3188bc295e7a0','S. Dreher.', '1', 'stdreher@hotmail.com');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (53, 66679, 'Losheim am See','Mühlengasse 86', 'Saarland','Merzig-Wadern',2,'49,518006','6,742028','2023/2023-07-04/Losheim_am_See-20230727123946-42186a11773f23862e83a2301dd3188bc295e7a0.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (53, '2023-07-04',NULL, '2023-07-04', '', '2023-07-11',  'F', 'F', '1', 0, 0, 1, 0, 53,'schon im letzten Jahr gemeldet 
Fundortbeschreibung Melder: im Garten
Alter Ablageordner: 2023/20230704 Losheim am See');
insert into melduser values (53,53,53);

--  54 - Kein Bild
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (54,  '1affb9d47dbedbb75180b4aba5ec8c84bc63d1c5','D. Drenske.', '1', 'info@biologenbuero-drenske.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (54, 14974, 'Ludwigsfelde','nördlich Brandenburgische Straße', 'Brandenburg','Teltow-Fläming',7,'52,320070','13,250460','');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (54, '2023-07-04',NULL, '2023-07-05', '', '2023-07-05',  'F', 'S', '2', 0, 0, 2, 0, 54,'Planungsbüro: sicherer Fund; Koordinaten geliefert 
Fundortbeschreibung Melder: Trockenrasenfläche
Alter Ablageordner: 2023/20230705 Ludwigsfelde
Kein Bild');
insert into melduser values (54,54,54);

--  55
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (55,  '4908281cc393490ef8f784b632ede1a1c6e8bb34','M. Ehrlilch.', '1', 'msehrlich1977@gmail.com');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (55, 15859, 'Storkow','Altstadt, Heinrich Heine Straße 60 ', 'Brandenburg','Oder-Spree',99,'52,258236','13,934985','2023/2023-07-05/Storkow-20230727123948-4908281cc393490ef8f784b632ede1a1c6e8bb34.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (55, '2023-07-05',NULL, '2023-07-05', '', '2023-07-11',  'F', 'F', '1', 0, 0, 1, 0, 55,'Koordinaten geliefert 
Fundortbeschreibung Melder: 
Alter Ablageordner: 2023/20230705 Storkow');
insert into melduser values (55,55,50);

--  56
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (56,  '4b887a2bd66586e6061ba0ac4c7eb1998b58dc29','L. Wenzel.', '1', 'lea-wenzel@gmx.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (56, 04924, 'Wildgrube','Domsdorfer Straße 12', 'Brandenburg','Elbe-Elster',99,'51,585780','13,3887163344998','2023/2023-07-07/Wildgrube-20230727123950-4b887a2bd66586e6061ba0ac4c7eb1998b58dc29.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (56, '2023-07-07',NULL, '2023-07-07', '', '2023-07-11',  'F', 'F', '1', 0, 0, 1, 0, 56,' 
Fundortbeschreibung Melder: 
Alter Ablageordner: 2023/20230707 Wildgrube');
insert into melduser values (56,56,56);

--  57
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (57,  '404186cd96e1e07d070e9b225d9e2508583bb07f','J. Hofmann.', '1', 'j.hofmann@gmx.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (57, 12524, 'Berlin','Alfonsstraße 48', 'Berlin','Berlin',2,'52,324751','13,417869','2023/2023-07-09/Blankenfelde_Mahlow_OT_Dahlewitz-20230727123952-34eeedfe4d29b3ffe5acbc33a1d34cc921105ecf.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (57, '2023-07-09',NULL, '2023-07-09', '',  '2023-07-17',  'F', 'F', '1', 0, 0, 1, 0, 57,' 
Fundortbeschreibung Melder: im Garten
Alter Ablageordner: 2023/20230709 Blankenfelde Mahlow OT Dahlewitz');
insert into melduser values (57,57,57);
-- 58

insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values ( 58,  'f0cbbe8df9ba7c777e7d2dbb55ab5b767dabd8c4','R. Rasch.', '1', 'rasch@medi-graph.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, longitude, latitude, ablage)
                          values (58, 15806, 'Zossen OT Dabendorf','Rangsdorfer Straße', 'Brandenburg','Teltow-Fläming',7,'52,252313','13,434112','2023/2023-07-08/Zossen_OT_Dabendorf-20230727123951-ae76d31d788f3a44b38ebf91f273269c3b633200.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (58, '2023-07-08',NULL, '2023-07-08', '', NULL,  'F', 'F', '1', 0, 0, 1, 0, 58,'Koordinaten geliefert 
Fundortbeschreibung Melder: Wiese
Alter Ablageordner: 2023/20230708 Zossen OT Dabendorf');

insert into melduser values (58,58,58);


-- 59
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values ( 59,  '1e87528494fc01084b026779e01e4a1e298047ce','M. Merl.', '1', 'markus_merl@physio-merl.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, longitude, latitude, ablage)
                          values (59, 15973, 'Schwielochsee OT Goyatz','Dorfstraße 14', 'Brandenburg','Potsdam-Mittelmark',99,'52,01821','14,175267','2023/2023-07-08/Schwielochsee_OT_Goyatz-20230727123951-8737b2814476e6851e356d021cc69ce8989bc9b4.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (59, '2023-07-08',NULL, '2023-07-08', '', NULL,  'F', 'F', '1', 0, 0, 1, 0, 59,'Koordinaten geliefert 
Fundortbeschreibung Melder: an Hauswand
Alter Ablageordner: 2023/20230708 Schwielochsee OT Goyatz');

insert into melduser values (59,59,59);

-- 60
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values ( 60,  '19bb6cb4fdaf2c8c839fc19d1002960d1eb484fd','H. Eger.', '1', 'hendrik.jeeger@web.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, longitude, latitude, ablage)
                          values (60, 03046, 'Cottbus','Ostrower Damm', 'Brandenburg','Cottbus',99,'51,757879','14,33937','2023/2023-07-09/Cottbus-20230727123951-dbf3132663ff8dec3684af1f63a466fb07c414db.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (60, '2023-07-09',NULL, '2023-07-09', '', NULL,  'F', 'F', '1', 0, 0, 1, 0, 60,'Koordinaten geliefert 
Fundortbeschreibung Melder: an Hauswand
Alter Ablageordner: 2023/20230709 Cottbus');

insert into melduser values (60,60,60);
-- 61

insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values ( 61,  '2c9aa1ea11de8eaf64a4fbe5ea1f006716309381','S. Camak.', '1', 'bybine@gmail.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, longitude, latitude, ablage)
                          values (61, 15827, 'Blankenfelde Mahlow OT Dahlewitz','Stubenrauchstraße 9', 'Brandenburg','Teltow-Fläming',2,'52,324751','13,417869','2023/2023-07-09/Blankenfelde_Mahlow_OT_Dahlewitz-20230727123952-34eeedfe4d29b3ffe5acbc33a1d34cc921105ecf.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (61, '2023-07-09',NULL, '2023-07-09', '', NULL,  'F', 'F', '1', 0, 0, 1, 0, 61,' 
Fundortbeschreibung Melder: im Garten
Alter Ablageordner: 2023/20230709 Blankenfelde Mahlow OT Dahlewitz');

insert into melduser values (61,61,61);

--  62
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (62,  'd53716b7b1c8e2a368e1289741214cce0a5572cc','B. Lehmann.', '1', 'lehmann-wiepersdorf@t-online.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (62, 14973, 'Wiepersdorf','Bettina-von-Arnim-Straße 1a', 'Brandenburg','Teltow-Fläming',99,'51,884649','13,240287','2023/2023-07-09/Wiepersdorf-20230727123953-d53716b7b1c8e2a368e1289741214cce0a5572cc.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (62, '2023-07-07',NULL, '2023-07-09', '',  '2023-07-17',  'F', 'F', '1', 0, 0, 1, 0, 62,' 
Fundortbeschreibung Melder: 
Alter Ablageordner: 2023/20230709 Wiepersdorf');
insert into melduser values (62,62,62);

--  63
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (63,  '5825daab60ae01e8d2b54b9d28b4c78f0fd1623d','T. Ziska.', '1', 'thomas.ziska@charite.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (63, 15537, 'Grünheide (Mark) OT Kienbaum','', 'Brandenburg','Oder-Spree',99,'52,446667','13,943611','2023/2023-07-10/Grunheide_Mark_OT_Kienbaum-20230727123954-5825daab60ae01e8d2b54b9d28b4c78f0fd1623d.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (63, '2023-07-08',NULL, '2023-07-10', '',  '2023-07-17',  'F', 'F', '3', 0, 0, 3, 0, 63,'Koordinaten geliefert, 3 Tiere gemeldet, eine durch Foto belegt aber alle drei sicher, da Artenkenner 
Fundortbeschreibung Melder: Erdgastrasse
Alter Ablageordner: 2023/20230710 Grünheide (Mark) OT Kienbaum');
insert into melduser values (63,63,63);

--  64
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (64,  '543c36eb62906fb73288c1b56a052c56a4f89b74','K. Werrstein.', '1', 'kiki030@gmx.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (64, 14558, 'Nuthetal OT Tremsdorf','Königsgraben', 'Brandenburg','Teltow-Fläming',99,'52,283822','13,135555','2023/2023-07-10/Nuthetal_OT_Tremsdorf-20230727123954-543c36eb62906fb73288c1b56a052c56a4f89b74.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (64, '2023-07-06',NULL, '2023-07-10', '',  '2023-07-17',  'F', 'F', '1', 0, 0, 1, 0, 64,'Koordinaten geliefert, Braunkehlchen frisst Mantis-Nymphe, siehe auch 20220820 Berlin 2 
Fundortbeschreibung Melder: NSG
Alter Ablageordner: 2023/20230710 Nuthetal OT Tremsdorf');
insert into melduser values (64,64,64);

--  65
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (65,  '0c9853a452d356ba20ac88e33036537cd1b5980e','D. Wiesner.', '1', 'daniwies@icloud.com');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (65, 04575, 'Neukieritzsch OT Lobstädt','Glück-Auf-Straße 65', 'Sachsen','Leipzig',99,'51,141619','12,448490','2023/2023-07-12/Neukieritzsch_OT_Lobstadt-20230728062036-a90ca2f2d751e11a1311ed4735eaf96180d96fed.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (65, '2022-08-01','2022-09-30', '2023-07-12', '', '2023-07-17',  'F', 'F', '2', 0, 2, 0, 0, 65,'Koordinaten geliefert, Zeitangabe 2022, August-September die meisten Sichtungen, genaue Funddaten der beiden Weibchen nicht bekannt, nachgehakt 
Fundortbeschreibung Melder: große Freifläche
Alter Ablageordner: 2023/20230712 Neukieritzsch OT Lobstädt');
insert into melduser values (65,65,65);

--  66
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (66,  '2c2a0ba32b13b0bc44aba4db05b5378440e3de11','D. Wiesner.', '1', 'daniwies@icloud.com');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (66, 04575, 'Neukieritzsch OT Lobstädt','Grenzstraße', 'Sachsen','Leipzig',99,'51,141975','12,447702','2023/2023-07-12/Neukieritzsch_OT_Lobstadt-20230728061507-ade3773e5124aa9a36440ea6905032a2d63a4924.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (66, '2023-07-12',NULL, '2023-07-12', '', '2023-07-17',  'F', 'F', '1', 0, 0, 1, 0, 66,'Koordinaten geliefert, Nachbarn von Frau Wiesner 
Fundortbeschreibung Melder: Hauswand
Alter Ablageordner: 2023/20230712 Neukieritzsch OT Lobstädt');
insert into melduser values (66,66,66);

--  67
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (67,  'dced32f6aaf0724c8bfd41142baa9b44b8d67d19','N. Geisler.', '1', 'geislernicolas@gmx.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (67, 14542, 'Werder (Havel)','Puschkinstraße 3c', 'Brandenburg','Potsdam-Mittelmark',99,'52,368365','12,922913','2023/2023-07-14/Werder_Havel-20230727215427-4cf85f8738fd3a075a6b22834070e19263f931db.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (67, '2022-08-25',NULL, '2023-07-14', '', '2023-07-17',  'F', 'F', '1', 1, 0, 0, 0, 67,' 
Fundortbeschreibung Melder: 
Alter Ablageordner: 2023/20230714 Werder (Havel)');
insert into melduser values (67,67,67);

--  68
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (68,  '097d8265bf0921f6eaef19206fe825c054524cc7','K. Rehfeld.', '1', 'kathi_maus86@yahoo.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (68, 15838, 'Am Mellensee OT Saalow','am Teich 1b', 'Brandenburg','Potsdam-Mittelmark',99,'52,191961','13,393576','2023/2023-07-15/Am_Mellensee_OT_Saalow-20230728062721-11dfb8add08acb8a0539d2d1c463204d2a3328cb.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (68, '2023-05-14',NULL, '2023-07-15', '', '2023-07-17',  'F', 'F', '1', 0, 0, 1, 0, 68,'siehe auch 20220806 Am Mellensee 
Fundortbeschreibung Melder: 
Alter Ablageordner: 2023/20230715 Am Mellensee OT Saalow');
insert into melduser values (68,68,68);

--  69
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (69,  '17b6f82a107c87ddefa61df5921307a50052a07b','M. Zaplata.', '1', 'mazaplata@gmail.com');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (69, 03116, 'Drepkau','Hühnerwasser', 'Brandenburg','Spree-Neiße',99,'???','???','2023/2023-07-15/Drepkau-20230728062728-9f8a6a690ac363c0416cb09b0794f174a863676b.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (69, '2023-07-12',NULL, '2023-07-15', '', '2023-07-17',  'F', 'F', '1', 0, 0, 1, 0, 69,'nachgehakt 
Fundortbeschreibung Melder: 
Alter Ablageordner: 2023/20230715 Drepkau');
insert into melduser values (69,69,69);

--  70
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (70,  'b61510c40dc79451e2e3936a537e21f711790f18','H. Kuritz.', '1', 'h.kurizt@online.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (70, 15907, 'Lübben (Spreewald)','Pakrstraße 6', 'Brandenburg','Dahme-Spreewald',99,'51,9431691505444','13,872671','2023/2023-07-15/Lubben_Spreewald-20230728062732-c0adec72eb082dca4162b73111b12ce7ee61177c.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (70, '2023-07-15',NULL, '2023-07-15', '', '2023-07-17',  'F', 'F', '1', 0, 0, 1, 0, 70,' 
Fundortbeschreibung Melder: Blumenbeet an der Neuapostolischen Kirche
Alter Ablageordner: 2023/20230715 Lübben (Spreewald)');
insert into melduser values (70,70,70);

--  71 nur ein Video mit geringer Auflösung
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (71,  '5bd0cd6c9f478b2f906945ad716a474e47d6243f','J. Nawrozki.', '1', 'j.naw@web.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (71, 14473, 'Potsdam','Michendorfer Chaussee 110', 'Brandenburg','Potsdam-Mittelmark',9,'52,363103','13,036265','');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (71, '2023-07-14',NULL, '2023-07-15', '',  '2023-07-17',  'F', 'F', '1', 0, 0, 1, 0, 71,'Koordinaten geliefert 
Fundortbeschreibung Melder: Kiesgrube BZR
Alter Ablageordner: 2023/20230715 Potsdam
Kein Bild, nur ein Video mit geringer Auflösung');
insert into melduser values (71,71,71);

--  72
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (72,  '9080ba91fbcab3c62c1ec02631d45208c57bd3ad','P. Sieder.', '1', 'peggysieder@googlemail.vom');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (72, 14959, 'Trebbin','Nuthestraße 30 ', 'Brandenburg','Teltow-Fläming',99,'52,222235','13,212031','2023/2023-07-15/Trebbin-20230727123959-9080ba91fbcab3c62c1ec02631d45208c57bd3ad.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (72, '2023-07-14',NULL, '2023-07-15', '', '2023-07-17',  'F', 'F', '1', 0, 0, 1, 0, 72,'Koordinaten geliefert 
Fundortbeschreibung Melder: 
Alter Ablageordner: 2023/20230414 Trebbin');
insert into melduser values (72,72,72);

--  73
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (73,  'fa027a43b320db9ce0ad795fe731ca03fef9c4e8','P. Jähnig.', '1', 'peggy.jaehnig@googlemail.com');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (73, 14974, 'Ludwigsfelde','Bordeauxweg 29', 'Brandenburg','Teltow-Fläming',2,'52,310418','13,208052','2023/2023-07-16/Ludwigsfelde-20230727123959-fa027a43b320db9ce0ad795fe631ca03fef9c4e8.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (73, '2023-07-15',NULL, '2023-07-16', '',  '2023-07-17',  'F', 'F', '1', 0, 0, 1, 0, 73,' 
Fundortbeschreibung Melder: Vorgarten
Alter Ablageordner: 2023/20230716 Ludwigsfelde');
insert into melduser values (73,73,73);

--  74
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (74,  'a887ea1e4666c5fe24e9b5bfae54e5bd7f58144c','C. Höring.', '1', 'norbert.katzschke@gmx.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (74, 14959, 'Trebbin','Kolonieweg 7', 'Brandenburg','Teltow-Fläming',2,'52,216587','13,181836','2023/2023-07-20/Trebbin-20230727221535-bf5382199dfea1920adbd01abf3c3a578f40e43c.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (74, '2023-07-15',NULL, '2023-07-20', '',  '2023-07-20',  'F', 'F', '1', 0, 0, 1, 0, 74,' 
Fundortbeschreibung Melder: im Garten
Alter Ablageordner: 2023/20230720 Trebbin');
insert into melduser values (74,74,74);

--  75
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (75,  '0df75f411e276d36b5e3363984f1c29ab26486d6','K. Rieke-Goetz.', '1', 'goetz@i-dsign.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (75, 14959, 'Trebbin OT Schönhagen','Schönhagener Gutshof 1', 'Brandenburg','Teltow-Fläming',1,'52,210859','13,146879','2023/2023-07-20/Trebbin_OT_Schonhagen-20230727124000-0df75f411e276d36b5e3363984f1c29ab26486d6.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (75, '2023-07-19','2023-07-20', '2023-07-20', '',  '2023-07-20',  'F', 'F', '2', 0, 0, 2, 0, 75,'ein Tier durch Foto belegt, eine zweite Nymphe von gestern mitgemeldet (ohne Foto) 
Fundortbeschreibung Melder: im Haus
Alter Ablageordner: 2023/20230720 Trebbin OT Schönhagen');
insert into melduser values (75,75,75);

--  76
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (76,  '2ad963e043c3b2bc96ac1d69013039b6dfa10443','L. Formann.', '1', 'lili.krueger@yahoo.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (76, 15806, 'Zossen OT Nächst Neuendorf','Wulzenweg 11', 'Brandenburg','Teltow-Fläming',99,'52,221514','13,421373','2023/2023-07-21/Zossen_OT_Nachst_Neuendorf-20230727124002-2ad963e043c3b2bc96ac1d69013039b6dfa10443.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (76, '2023-07-20',NULL, '2023-07-21', '', '2023-07-21' ,  'F', 'F', '1', 0, 0, 1, 0, 76,' 
Fundortbeschreibung Melder: am Haus
Alter Ablageordner: 2023/20230721 Zossen OT Nächst Neuendorf');
insert into melduser values (76,76,76);

--  77
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (77,  '092e76d7f1c3357e31c2b3640264f773f9fddf48','T. Schulz.', '1', 'tina.schulz@gymln.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (77, 15910, 'Schönwalde','', 'Brandenburg','Dahme-Spreewald',99,'???','???','2023/2023-07-21/Schonwalde-20230727124003-092e76d7f1c3357e31c2b3640264f773f9fddf48.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (77, '2023-07-21',NULL, '2023-07-21', '', '2023-07-21',  'F', 'F', '1', 0, 0, 1, 0, 77,'nachgehakt 
Fundortbeschreibung Melder: am Haus
Alter Ablageordner: 2023/20230721 Schönwalde');
insert into melduser values (77,77,77);


--  78
insert into users (id, user_id, user_name, user_rolle, user_kontakt) 
                          values (78,  '59d17a5d193ae5c3fe95e19271428aa78c2e0761','W T.', '1', 'wolftristan16@gmail.com');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                          values (78, 15848, 'Friedland','Oelsen 26', 'Brandenburg','',99,'52.13248','14.38379','2023/2023-07-27/Friedland-20230727235708-59d17a5d193ae5c3fe95e19271428aa78c2e0761-1.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                          values (78, '2023-07-27','2023-07-27', '2023-07-27', '', NULL,  'F', 'F', '1', 0, 0, 1, 0, 78,'In Nähe von hohem Gras auf einem Haufen von Stücken von Bäumen (Kiefer etc.)');
insert into melduser values (78,78,78);

