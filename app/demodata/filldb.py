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

def insert_data_reports(db):
    """A set of twenty reports for testing"""


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
        "insert into fundorte values (1 , '64027', 'Miesbach', 'Karl Heinz-Ring-Straße','Ville', 'Hamburg', '', '', 1, '10.671282', '52.036639', '2025/2025-01-19/mantis1.webp');",
        "insert into fundorte values (2 , '76960', 'Osterode am Harz', 'Lübsstr. ','Ville', 'Niedersachsen', '', '', 1, '8.480548', '50.777494', '2025/2025-01-19/mantis2.webp');",
        "insert into fundorte values (3 , '17557', 'Kusel', 'Mendestr. ','Ville', 'Bremen', '', '', 1, '8.002667' , '49.039553', '2025/2025-01-19/mantis3.webp');",
        "insert into fundorte values (4 , '73949', 'Bad Mergentheim', 'Stolzestr. ','Ville', 'Hamburg', '', '', 1, '12.241585', '51.746216', '2025/2025-01-19/mantis4.webp');",
        "insert into fundorte values (5 , '38203', 'Niesky', 'Kadestraße ','Ville', 'Saarland', '', '', 1, '10.217125', '50.980799', '2025/2025-01-19/mantis5.webp');",
        "insert into fundorte values (6 , '25639', 'Hünfeld', 'Regine-Junck-Ring ','Ville', 'Schleswig-Holstein', '', '', 1, '11.912951', '51.522037', '2025/2025-01-19/mantis6.webp');",
        "insert into fundorte values (7 , '43619', 'Eichstätt', 'Wenke-Wohlgemut-Ring ','Ville', 'Berlin', '', '', 1, '9.054942' , '52.930573', '2025/2025-01-19/mantis1.webp');",
        "insert into fundorte values (8 , '67355', 'Sangerhausen', 'Marcel-Wernecke-Allee ','Ville', 'Schleswig-Holstein', '', '', 1, '11.129620', '52.884420', '2025/2025-01-19/mantis2.webp');",
        "insert into fundorte values (9 , '13669', 'Gotha', 'Helfried-Holsten-Gasse','Ville', 'Sachsen-Anhalt', '', '', 1, '8.725520' , '49.045359', '2025/2025-01-19/mantis3.webp');",
        "insert into fundorte values (10, '78867', 'Göppingen', 'Briemerallee ','Ville', 'Nordrhein-Westfalen', '', '', 1, '10.922293', '53.113956', '2025/2025-01-19/mantis4.webp');",
        "insert into fundorte values (11, '81160', 'Seelow', 'Imke-Klemt-Straße ','Ville', 'Saarland', '', '', 1, '11.005462', '51.076435', '2025/2025-01-19/mantis5.webp');",
        "insert into fundorte values (12, '51261', 'Uelzen', 'Betina-Bachmann-Allee ','Ville', 'Rheinland-Pfalz', '', '', 1, '10.331594', '53.545572', '2025/2025-01-19/mantis6.webp');",
        "insert into fundorte values (13, '32447', 'Schwerin', 'Paffrathring ','Ville', 'Nordrhein-Westfalen', '', '', 1, '11.281252', '52.694736', '2025/2025-01-19/mantis1.webp');",
        "insert into fundorte values (14, '75971', 'München', 'Eckehard-Eberth-Allee ','Ville', 'Saarland', '', '', 1, '10.053301', '53.430086', '2025/2025-01-19/mantis2.webp');",
        "insert into fundorte values (15, '51366', 'Lübben', 'Kathrin-Eckbauer-Ring ','Ville', 'Berlin', '', '', 1, '12.595564', '51.244785', '2025/2025-01-19/mantis3.webp');",
        "insert into fundorte values (16, '40483', 'Güstrow', 'Fredy-Schüler-Allee ','Ville', 'Sachsen', '', '', 1, '10.200889', '51.180463', '2025/2025-01-19/mantis4.webp');",
        "insert into fundorte values (17, '75034', 'Prenzlau', 'Stumpfring ','Ville', 'Hessen', '', '', 1, '8.050120' , '52.471399', '2025/2025-01-19/mantis5.webp');",
        "insert into fundorte values (18, '95649', 'Neustrelitz', 'Jacobi Jäckelstr. ','Ville', 'Mecklenburg-Vorpommern', '', '', 1, '11.194988', '53.041214', '2025/2025-01-19/mantis6.webp');",
        "insert into fundorte values (19, '85601', 'Feuchtwangen', 'Tlustekring ','Ville', 'Niedersachsen', '', '', 1, '12.819640', '51.769984', '2025/2025-01-19/mantis1.webp');",
        "insert into fundorte values (20, '34756', 'Jülich', 'Sergei-Naser-Straße ','Ville', 'Bayern', '', '', 1, '10.555141', '53.610359', '2025/2025-01-19/mantis2.webp');"
    ]
    
    meldungen = [
        "insert into meldungen values (1, NULL, '2025-10-03', NULL, '2025-02-01', NULL, NULL, 1, 1, 0, 0, 0, 0, 1,  'F', '', 'Antworten vielleicht zusammen langsam sind möglich heute. Boden darauf Zeit alle reich Wiese. Jetzt legen Erde möglich jetzt Jahr spät rot.', '');",
        "insert into meldungen values (2, NULL, '2025-08-24', NULL, '2025-02-01', NULL, NULL, 1, 0, 0, 1, 0, 0, 2,  'F', '', 'Das Ball viel. Glauben Schluss rechnen Wetter. Stadt ab Monat Land selbst suchen merken.\nSchreiben Spiel schwer Frage. Junge in Zug nichts Wiese Weihnachten auf.', '');",
        "insert into meldungen values (3, NULL, '2025-04-26', NULL, '2025-02-01', NULL, NULL, 1, 0, 1, 0, 0, 0, 3,  'F', '', 'Gott ihn Finger verstecken Papa Affe. Die dabei Baum antworten.\nZurück mein durch Winter weiter. Ferien früher Baum Sonntag. Hoch schlagen aus.', '');",
        "insert into meldungen values (4, NULL, '2025-01-02', NULL, '2025-02-01', NULL, NULL, 1, 0, 0, 1, 0, 0, 4,  'F', '', 'Arzt grün eigentlich gefährlich dürfen nein. Haare Monate neu hören arbeiten. Also Zug den Eis.\nNicht halten setzen.\nTier Land dafür also Klasse. Mädchen heute sich wird damit.', '');",
        "insert into meldungen values (5, NULL, '2025-10-18', NULL, '2025-02-02', NULL, NULL, 1, 0, 0, 0, 1, 0, 5,  'F', '', 'Schluss Glas halbe Papa nehmen Monate spielen.\nBeispiel um Wasser Familie verstecken können Wiese also. Dir gefährlich rennen Glück.', '');",
        "insert into meldungen values (6, NULL, '2025-01-28', NULL, '2025-02-02', NULL, NULL, 1, 1, 0, 0, 0, 0, 6,  'F', '', 'Heute Vater natürlich nichts. Kommen nimmt lernen hängen. Es zeigen Schiff zurück bekommen danach Küche. Heiß fressen leise Oma.', '');",
        "insert into meldungen values (7, NULL, '2022-08-10', NULL, '2025-02-02', NULL, NULL, 1, 0, 0, 1, 0, 0, 7,  'F', '', 'Warm genau wir Stelle böse. Ruhig gewinnen helfen sein Straße öffnen so. Weg dir schwimmen hart.\nDunkel nie stellen können hoch hart schaffen. Angst See besser.', '');",
        "insert into meldungen values (8, NULL, '2025-12-25', NULL, '2025-02-01', NULL, NULL, 1, 0, 0, 0, 1, 0, 8,  'F', '', 'Geschenk weg gehen sieben Maus mit. Schule Bein fragen Wohnung heraus Wald Teller.\nDauern Beispiel Spaß wenig. Vorbei fünf Ende Gott lernen spielen ihn.', '');",
        "insert into meldungen values (9, NULL, '2025-09-30', NULL, '2025-02-01', NULL, NULL, 1, 0, 0, 1, 0, 0, 9,  'F', '', 'Lustig Stück nichts. Onkel neun Katze Baum einigen darauf.\nMann deshalb lassen weg fragen nimmt fröhlich zeigen. Kennen tief Straße überall jetzt Zahl fertig. Haus lange sechs.', '');",
        "insert into meldungen values (10,NULL, '2022-09-04', NULL, '2025-02-01', NULL, NULL, 1, 0, 0, 0, 1, 0, 10, 'F', '', 'Voll darauf nämlich sehen Geschichte. Minute nennen Land kalt. Dabei Lehrer singen kochen sechs schreiben jung brauchen. Wohnung werfen neben überall.', '');",
        "insert into meldungen values (11,NULL, '2022-09-24', NULL, '2025-02-01', NULL, NULL, 1, 0, 1, 0, 0, 0, 11, 'F', '', 'Stunde drei fressen springen ins an. Pferd nennen stellen bis wer Geschichte. Schwester Brief Ball sie brauchen stehen.', '');",
        "insert into meldungen values (12,NULL, '2025-11-18', NULL, '2025-02-01', NULL, NULL, 1, 0, 0, 0, 1, 0, 12, 'F', '', 'Grün fertig so. Maus ihr schlagen nur damit lernen. Krank schreien zusammen Spiel gleich lesen Weg.\nStelle will das kommen Leben Wagen Abend schlafen. Pferd nein weiter schnell.', '');",
        "insert into meldungen values (13,NULL, '2025-02-12', NULL, '2025-02-01', NULL, NULL, 1, 0, 0, 1, 0, 0, 13, 'F', '', 'Dich ihr Land Garten stellen. Tun kein vor oben.\nSpäter her alle nach Flasche schreien was arbeiten.', '');",
        "insert into meldungen values (14,NULL, '2020-02-19', NULL, '2025-02-01', NULL, NULL, 1, 1, 0, 0, 0, 0, 14, 'F', '', 'Geld haben packen dick fallen Mädchen kalt. Luft wichtig schaffen.\nOma ließ tun. Drehen laut Herz den. Garten sind gestern Leute Geld.', '');",
        "insert into meldungen values (15,NULL, '2025-09-03', NULL, '2025-02-01', NULL, NULL, 1, 0, 1, 0, 0, 0, 15, 'F', '', 'Schicken sonst Mama stellen sagen an.\nHin fertig Spaß blau. Rot treffen mit.\nGleich beißen aus weiter ohne holen Flasche. Glück am gab hier hinter kam.', '');",
        "insert into meldungen values (16,NULL, '2025-10-15', NULL, '2025-02-01', NULL, NULL, 1, 0, 0, 0, 1, 0, 16, 'F', '', 'Zeigen fährt reiten singen so. Neben sonst Name Junge waschen. Dauern schlafen Haare Wasser Flasche. Stelle was dem las wirklich Monat scheinen.', '');",
        "insert into meldungen values (17,NULL, '2020-11-23', NULL, '2025-02-01', NULL, NULL, 1, 0, 0, 1, 0, 0, 17, 'F', '', 'Sache gestern fliegen heißen damit Schiff. Tür allein gesund reich vom heiß. Garten zeigen Stein jung Brief sehr klein.', '');",
        "insert into meldungen values (18,NULL, '2025-12-31', NULL, '2025-02-01', NULL, NULL, 1, 0, 1, 0, 0, 0, 18, 'F', '', 'Schlimm Leute singen ohne zur andere mich Ferien. Wenn sind bleiben sehen Bruder gleich schon ging. Bringen ja man gestern Stein bringen weiß.\nRuhig von Glas immer sein war.', '');",
        "insert into meldungen values (19,NULL, '2025-12-23', NULL, '2025-02-02', NULL, NULL, 1, 0, 0, 0, 1, 0, 19, 'F', '', 'Dann gar Teller schön waschen vor Nase. Lehrer Maus fehlen dann.\nVogel ihm Sommer bis hin schlagen frei.\nAls kochen dir sagen mehr. Fast wenn antworten wer.', '');",
        "insert into meldungen values (20,NULL, '2025-01-20', NULL, '2025-02-01', NULL, NULL, 1, 0, 1, 0, 0, 0, 20, 'F', '', 'hrrad spät müde mit. Zeit zurück Rad mögen den.\nHelfen Loch sonst mich. Aus Stelle allein fiel ließ böse machen. Denn Tag neun bald Rad.', '');"
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

   
    for user in users:
        db.session.execute(
            text(user)
        )
    for fundort in fundorte:
        db.session.execute(
            text(fundort)
        )

    for meldung in meldungen:
        db.session.execute(
            text(meldung)
        )
        
    for melduser in meldusers:
        db.session.execute(
            text(melduser)
        )


    db.session.commit()
