for i in range(100,600):
    num = i  
    template = f"""
-- {num} ----------------
insert into users (id, user_id, user_name, user_rolle, user_kontakt)
                    values ( {num},  '10000','Tester T.', '1', 'tester@exampe.de');
insert into fundorte (id, plz, ort, strasse, land, kreis, beschreibung, latitude, longitude, ablage)
                    values ({num}, 111111, 'Testort','Testallee 66', 'Brandenburg','',7,'52.0000','12.0000','2023/2023-08-28/Irgendow-20230828235708-10000.webp');
INSERT INTO meldungen (id, dat_fund_von, dat_fund_bis, dat_meld, bearb_id, dat_bear, fo_quelle, fo_beleg, art_m, art_w, art_n, art_o, art_f, fo_zuordnung, anm_melder)
                    values ({num}, '2023-08-28',NULL, '2023-08-28', '', NULL,  'F', 'F', '1', 0, 0, 1, 0, {num},'Ein kleiner Kommentar vom Tester.');
INSERT INTO melduser (id, id_meldung, id_user)
                    values({num},{num},{num});
"""
    print(template)
