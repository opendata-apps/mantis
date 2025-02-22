from sqlalchemy import text

def generatat_sample_data():

    """
    Generate 500 uniqe datasets for testing as SQL statements.
    See also fill-db2.py for better testdata.
    """
    
    for i in range(100, 600):
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

    

        
def insert_data_reports(session):
    """A set of twenty reports for testing"""

    stm = """

with sequences as (
  select *
  from (
    select table_schema,
           table_name,
           column_name,
           pg_get_serial_sequence(format('%I.%I', table_schema, table_name), column_name) as col_sequence
    from information_schema.columns
    where table_schema not in ('pg_catalog', 'information_schema')
  ) t
  where col_sequence is not null
), maxvals as (
  select table_schema, table_name, column_name, col_sequence,
          (xpath('/row/max/text()',
             query_to_xml(format('select max(%I) from %I.%I', column_name, table_schema, table_name), true, true, ''))
          )[1]::text::bigint as max_val
  from sequences
) 
select table_schema, 
       table_name, 
       column_name, 
       col_sequence,
       coalesce(max_val, 0) as max_val,
       setval(col_sequence, coalesce(max_val, 1)) --<< this will change the sequence
from maxvals;

    """ 


    users =[
        "insert into users values (1 , '9999', 'Geisel K.'      ,9,  'rspiess@example.net');", 
        "insert into users values (2 , 'e40adafa23250fdd5024c9887544317a1101534d', 'Graf K.'        ,2,  '');", 	       	       	      
        "insert into users values (3 , 'f04ad4e0b099b6404b1ccda0af0282cf49693b43', 'Kabus J.'       ,1,  ';errmann29@example.com');",
        "insert into users values (4 , '4c4d45b1964c8d949702384756f33b64d37a5d3c', 'Stolze R.'      ,2,  '');",      
        "insert into users values (5 , '5843c1093f94be44442ff876cac6185a2d36310e', 'Lübs S.'        ,1,  'arndbarkholz@example.com');", 
        "insert into users values (6,  '972a6f09f79e095c5ecfa78bc499de28c61b8849', 'Sager H.'       ,2,  '');",      
        "insert into users values (7,  '264aca7e20e15aa2401f042dceed384da6d7747a', 'Klemm T.'       ,1,  'eruppersberger@example.org');",
        "insert into users values (8,  'a779e1ef972b987744795a60fcda91ee94b03ebc', 'Ruppersberg B.' ,2,  '');",		       
        "insert into users values (9 , '2ab71517482f824f925d09b9aa6e387df99befa7', 'Junken H.'      ,1,  'rosenowgerlinde@example.net');",
        "insert into users values (10, 'abf240ca94b47150b263789e33558023492fd2a1', 'Kallert Z.'     ,2,  '');",		       
        "insert into users values (11, '874208b1da349f20a88862f38a856bd711c2e165', 'Gute C.'        ,1,  'fmende@example.net');",	       
        "insert into users values (12, 'a4b2a7930d116dc0d95ada297a6e05e6827d3c49', 'Tlustek H.'     ,2,  '');",	      	      
        "insert into users values (13, '1fb0cfb0be3b0c75c537a50c57e0060ba8b6837e', 'Boucsein K.'    ,1,  'henrikullmann@example.com');",
        "insert into users values (14, '119699d4271239e54c73a88763dc4dc70d6a4692', 'Pieper U.'      ,2,  '');",		      
        "insert into users values (15, 'c56fe0b6262dc626a5faf21c55b1f34f7babcfb1', 'Beer N.'        ,1,  'edwardschleich@example.org');",
        "insert into users values (16, '294eb5a4d547b7f662d8d6eb053de5d89c9598e7', 'Mude I.'        ,2,  '');",		      
        "insert into users values (17, '2d7345fd039eaef8796047c61ab760cac52b67e4', 'Anders R.'      ,1,  'nikoschwital@example.net');", 
        "insert into users values (18, 'de275fd3b5518f495b46bc6741329a3fbf42cbfb', 'Mies A.'        ,2,  '');",		      
        "insert into users values (19, '9b9d6a941dea27e46f4e5c79284f7df4c82fca49', 'Stey R.'        ,1,  'pfoerster@example.net');",    
        "insert into users values (20, '1ba4729cde055af39bd148b533440eb36854fed6', 'Schüler H.'     ,2,  '');",		      
        "insert into users values (21, 'a88de66aa7976cb7990af54c16c0fd2c067515f9', 'Reuter A.'      ,1,  'xgrein-groth@example.org');", 
        "insert into users values (22, '17bf510cb2cd5cc737b0c6e5d96d2bd4a5cb2166', 'Losekann Z.'    ,2,  '');",		      
        "insert into users values (23, 'd2c830fd84ccabe149aff154c5e1ddcef662f052', 'Henck H.'       ,1,  'corneliuswilmsen@example.org');",
        "insert into users values (24, 'c18cb94b7faac3fff2bf5f00f8d33857eabe2b62', 'Kranz H.'       ,2,  '');",		      	
        "insert into users values (25, '0c7571741c04d2365aa7816efd298e8df9091122', 'Schwital S.'    ,1,  'ndobes@example.com');",	       	
        "insert into users values (26, '4d83cfb96b5fa3bb80f714c48b5e031f4cf3a96b', 'Weihmann B.'    ,2,  '');",	      	      
        "insert into users values (27, '166bc2da77cb1d6e9a07f3d6fd61c841b394f3c6', 'Kaul D.'        ,1,  'tlustekellinor@example.com');",
        "insert into users values (28, '4b59ec4e73091ff5a5c407618e986f92c138f2fb', 'Schacht H.'     ,2,  '');",		      
        "insert into users values (29, '6325e4e69ee6789a7aa0ebb9a0e0b63cdf67795a', 'Biggen L.'      ,1,  'peterpaertzelt@example.com');",
        "insert into users values (30, '82ecb28dad4e085005642b680f7f736e328c9708', 'Reinhardt C.'   ,2,  '');",		      
        "insert into users values (31, '086cd63464247668799cc5a508235012b64a4bf9', 'Stroh M.'       ,1,  'rosenowcarsten@example.net');",
        "insert into users values (32, '60f0cfe6daa379e67a3b66e4c89cc5f60d10ef75', 'Schweitzer F.'  ,2,  '');",		      
        "insert into users values (33, 'a1a0c14a53b7bbd010fc48ab2ac42d35d959d2b8', 'Täsche T.'      ,1,  'cbender@example.org');",             
        "insert into users values (34, 'e23db69d73b65d6c8006f928d242a793ccde72f2', 'Kaul K.'        ,2,  '');",	       	      
        "insert into users values (35, '5f4a7fec84fb0801a5157cf1ce41835774a92704', 'Gute M.'        ,1,  'reinhildknappe@example.org');",
        "insert into users values (36, 'd55655a3223d58bf0f76069e10c01a6f22e117ee', 'Rogge C.'       ,2,  '');",		      
        "insert into users values (37, '7228ef93c5b4347ffdcfe63d77bd8617fdb080e5', 'Geißler B.'     ,1,  'detlev23@example.org');",     
        "insert into users values (38, '2891d752d2d493ee0e95791da0d1528c49876882', 'Trub L.'        ,2,  '');",		      
        "insert into users values (39, 'c56782d029b8a62160175fd7112b74f573cd101f', 'Putz B.'        ,1,  'sandrobohnbach@example.com');",
        "insert into users values (40, 'f6ebc5f7cdc4dcd125a095731a95b66117e533bd', 'Bärer R.'       ,2,  '');"

    ]
    
    fundorte = [
        "insert into fundorte values (1 , '64027', 'Zossen', 'Oertelufer','Zossen', 'Teltow-Fläming', '12072477', '3746', 1, '13.440683', '52.217574', '2025/2025-01-19/mantis1.webp');",
        "insert into fundorte values (2 , '14793', 'Ziesar', 'Wiesenweg','Potsdam-Mittelmark', 'Brandenburg', '12069696', '3739', 1, '12.281342', '52.257955', '2025/2025-01-19/mantis2.webp');",
        "insert into fundorte values (3 , '03044', 'Cottbus', 'Querstraße 14','Schmellwitz', 'Brandenburg', '12052000', '4251', 1, '14.322739' , '51.785667', '2025/2025-01-19/mantis3.webp');",
        "insert into fundorte values (4 , '14929', 'Treuenbrietzen', 'Brücker Straße','Potsdam-Mittelmark', 'Brandenburg', '12069632', '3843', 1, '12.241585', '51.746216', '2025/2025-01-19/mantis4.webp');",
        "insert into fundorte values (5 , '16928', 'Pritzwalk', 'Bahnhofstraße 23','Prignitz', 'Brandenburg', '12070316', '2839', 1, '12.183323', '53.146346', '2025/2025-01-19/mantis5.webp');",
        "insert into fundorte values (6 , '06116', 'Halle (Saale)', 'Messestraße','Kanena/Bruckdorf', 'Sachsen-Anhalt', '15002000', '4538', 1, '11.912951', '51.522037', '2025/2025-01-19/mantis6.webp');",
        "insert into fundorte values (7 , '04936', 'Fichtwald', 'Dorfstraße 8','Elbe-Elster', 'Brandenburg', '12062134', '4246', 1, '13.440228' , '51.738052', '2025/2025-01-19/mantis1.webp');",
        "insert into fundorte values (8 , '14943', 'Luckenwalde', 'Meisterweg','Teltow-Fläming', 'Brandenburg', '12072232', '3945', 1, '13.174152', '52.080641', '2025/2025-01-19/mantis2.webp');",
        "insert into fundorte values (9 , '03050', 'Cottbus', 'Franz-Schubert-Straße 20','Madlow', 'Brandenburg', '12052000', '4252', 1, '14.348145' , '51.722646', '2025/2025-01-19/mantis3.webp');",
        "insert into fundorte values (10, '16259', 'Bad Freienwalde (Oder)', 'Wriezener Straße','Märkisch-Oderland', 'Brandenburg', '12064044', '3250', 1, '14.044991', '52.780902', '2025/2025-01-19/mantis4.webp');",
        "insert into fundorte values (11, '10719', 'Berlin', 'Pfalzburger Straße 23','Charlottenburg-Wilmersdorf', 'Berlin', '11000004', '3545', 1, '13.320923', '52.493207', '2025/2025-01-19/mantis5.webp');",
        "insert into fundorte values (12, '15234', 'Frankfurt (Oder)', 'Riebestraße 5','Rosengarten/Pagram', 'Brandenburg', '12053000', '3652', 1, '14.487534', '52.350483', '2025/2025-01-19/mantis6.webp');",
        "insert into fundorte values (13, '14548', 'Caputh', 'Schmerberger Weg 92a','Potsdam-Mittelmark', 'Brandenburg', '12069590', '4547', 1, '13.540649' , '51.464414', '2025/2025-01-19/mantis5.webp');",
        "insert into fundorte values (14, '21217', 'Seevetal', 'Rehmendamm 49a','Harburg', 'Niedersachsen', '', '', 1, '10.053864', '53.428226', '2025/2025-01-19/mantis2.webp');",
        "insert into fundorte values (15, '04289', 'Leipzig', 'Russenstraße 146','Leipzig', 'Sachsen', '14713000', '4640', 1, '12.447510', '51.302603', '2025/2025-01-19/mantis3.webp');",
        "insert into fundorte values (16, '12349', 'Berlin', 'Warmensteinacher Straße 1','Neukölln', 'Berlin', '11000008', '3546', 1, '13.428040', '52.419952', '2025/2025-01-19/mantis4.webp');",
        "insert into fundorte values (17, '04910', 'Elsterwerda', 'An den Kanitzen 6','Elbe-Elster', 'Brandenburg', '12062124', '4547', 1, '13.540649' , '51.464414', '2025/2025-01-19/mantis5.webp');",
        "insert into fundorte values (18, '14913', 'Jüterbog', 'Ettmüllerstraße','Teltow-Fläming', 'Brandenburg', '12072169', '4044', 1, '13.075104', '51.996576', '2025/2025-01-19/mantis6.webp');",
        "insert into fundorte values (19, '06917', 'Jessen (Elster)', 'Lindenstraße 41','Wittenberg', 'Sachsen-Anhalt', '15091145', '4243', 1, '12.958374', '51.785129', '2025/2025-01-19/mantis1.webp');",
        "insert into fundorte values (20, '14662', 'Friesack', 'Industriegelände', 'Havelland','Brandenburg', '12063088', '3241', 1, '12.575226', '52.730663', '2025/2025-01-19/mantis2.webp');"
    ]
    
    meldungen = [
        "insert into meldungen values (1, NULL, '2024-10-03', NULL, '2025-02-01', '2025-02-03', '9999', 1, 1, 0, 0, 0, 0, 1,  'F', '', 'Lieber arm ab, als arm dran.', '');",
        "insert into meldungen values (2, NULL, '2024-08-24', NULL, '2025-02-01', NULL, NULL, 1, 0, 0, 1, 0, 0, 2,  'F', '', 'Lieber ein Ende mit Schrecken, als ein Schrecken ohne Ende.', '');",
        "insert into meldungen values (3, NULL, '2024-04-26', NULL, '2025-02-01', NULL, NULL, 1, 0, 1, 0, 0, 0, 3,  'F', '', 'Lieber ehrlich verlieren, als unehrlich gewinnen.', '');",
        "insert into meldungen values (4, NULL, '2024-01-02', NULL, '2025-02-01', NULL, NULL, 1, 0, 0, 1, 0, 0, 4,  'F', '', 'Lieber dumm gefragt, als dumm geblieben.', '');",
        "insert into meldungen values (5, NULL, '2024-10-18', NULL, '2025-02-02', NULL, NULL, 1, 0, 0, 0, 1, 0, 5,  'F', '', 'Lieber spät als nie.', '');",
        "insert into meldungen values (6, NULL, '2024-01-28', NULL, '2025-02-02', '2025-02-02', '9999', 1, 1, 0, 0, 0, 0, 6,  'F', '', 'Lieber den Spatz in der Hand, als die Taube auf dem Dach.', '');",
        "insert into meldungen values (7, NULL, '2024-08-10', NULL, '2025-02-02', NULL, NULL, 1, 0, 0, 1, 0, 0, 7,  'F', '', 'Lieber gut drauf, als drauf gemacht.', '');",
        "insert into meldungen values (8, NULL, '2024-12-25', NULL, '2025-02-01', '2025-02-03', '9999', 1, 0, 0, 0, 1, 0, 8,  'F', '', 'Lieber ein guter Freund, als tausend Bekannte.', '');",
        "insert into meldungen values (9, NULL, '2024-09-30', NULL, '2025-02-01', NULL, NULL, 1, 0, 0, 1, 0, 0, 9,  'F', '', 'Lieber keinen Plan, als keinen Humor.', '');",
        "insert into meldungen values (10,NULL, '2024-09-04', NULL, '2025-02-01', NULL, NULL, 1, 0, 0, 0, 1, 0, 10, 'F', '', 'Lieber einmal lachen, als tausendmal nicken.', '');",
        "insert into meldungen values (11,'t', '2024-09-24', NULL, '2025-02-01', NULL, NULL, 1, 0, 1, 0, 0, 0, 11, 'F', '', 'Gelöscht, nicht angenommen.', '');",
        "insert into meldungen values (12,NULL, '2024-11-18', NULL, '2025-02-01', NULL, NULL, 1, 0, 0, 0, 1, 0, 12, 'F', '', 'Lieber eine Stunde in guter Gesellschaft, als eine Woche allein.', '');",
        "insert into meldungen values (13,NULL, '2024-02-12', NULL, '2025-02-01', NULL, NULL, 1, 0, 0, 1, 0, 0, 13, 'F', '', 'Ungenaue Meldung Koordinten und Ortsangabe weichen voneinader ab.\n sind identisch mit Elsterwerda', '');",
        "insert into meldungen values (14,NULL, '2024-02-19', NULL, '2025-02-01', NULL, NULL, 1, 1, 0, 0, 0, 0, 14, 'F', '', 'Lieber einen guten Ruf, als viel Geld.', '');",
        "insert into meldungen values (15,NULL, '2024-09-03', NULL, '2025-02-01', NULL, NULL, 1, 0, 1, 0, 0, 0, 15, 'F', '', 'Lieber einen Berg erklimmen, als im Tal verharren.', '');",
        "insert into meldungen values (16,NULL, '2024-10-15', NULL, '2025-02-01', NULL, NULL, 1, 0, 0, 0, 1, 0, 16, 'F', '', 'Lieber das Leben leben, als die Zeit zählen.', '');",
        "insert into meldungen values (17,NULL, '2024-11-23', NULL, '2025-02-01', NULL, NULL, 1, 0, 0, 1, 0, 0, 17, 'F', '', 'Lieber nicht perfekt, als gar nicht.', '');",
        "insert into meldungen values (18,NULL, '2024-12-31', NULL, '2025-02-01', NULL, NULL, 1, 0, 1, 0, 0, 0, 18, 'F', '', 'Lieber einmal um den Block laufen, als nie den Weg finden.', '');",
        "insert into meldungen values (19,NULL, '2024-12-23', NULL, '2025-02-02', NULL, NULL, 1, 0, 0, 0, 1, 0, 19, 'F', '', 'Lieber einmal um den Block laufen, als nie den Weg finden.', '');",
        "insert into meldungen values (20,NULL, '2024-01-20', NULL, '2025-02-01', NULL, NULL, 1, 0, 1, 0, 0, 0, 20, 'F', '', 'Lieber ein Ende mit Weinen, als ein Leben ohne Lachen.', '');"
    ]
    
    meldusers = [
        "insert into melduser values (1,1,1,2);",    
        "insert into melduser values (2,2,3,4);",    
        "insert into melduser values (3,3,5,6);",          
        "insert into melduser values (4,4,7,8);",          
        "insert into melduser values (5,5,9,10);",        
        "insert into melduser values (6,6,11,12);",  
        "insert into melduser values (7,7,13,14);",  
        "insert into melduser values (8,8,15,16);",  
        "insert into melduser values (9,9,17,18);",  
        "insert into melduser values (10,10,19,20);",
        "insert into melduser values (11,11,21,22);",
        "insert into melduser values (12,12,23,24);",
        "insert into melduser values (13,13,25,26);",
        "insert into melduser values (14,14,27,28);",
        "insert into melduser values (15,15,29,30);",
        "insert into melduser values (16,16,31,32);",
        "insert into melduser values (17,17,33,34);",
        "insert into melduser values (18,18,35,36);",
        "insert into melduser values (19,19,37,38);",
        "insert into melduser values (20,20,39,40);",
    ]

    # insert data
    for user in users:
        session.execute(
            text(user)
        )
    for fundort in fundorte:
        session.execute(
            text(fundort)
        )

    for meldung in meldungen:
        session.execute(
            text(meldung)
        )
        
    for melduser in meldusers:
        session.execute(
            text(melduser)
        )
    session.commit()

    # update all sequences for all tables
    session.execute(
            text(stm)
        )
    session.commit()    
