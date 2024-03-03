"""

   x-------o  o-------o o-------o o-------o o-------o o-------o
   |       |  |       | |       | |       | |       | |       |
   | 0502  |  |  ...  | | 0519  | | 0520  | | 0521  | | ...   |
   |       |  |       | |       | |       | |       | |       |
   o-------o  o-------o o-------o o-------o o-------o o-------o                                                            
                                                              
   o-------o                          ^                                   
   |       |                          |                   
   | ...   |                          |                   
   |       |                          o--- nördlichste    
   o-------o                               Meßtischblätter
                                                          
   o-------o   x = Nullpunkt  55.49839, 6.0                       
   |       |                                              
   | 4101  |  <-- Meßtischblatte am weitesten im Westen   
   |       |                                              
   o-------o   
               
   o-------o
   |       |   
   | ...   |   
   |       |   
   o-------o   
               
"""


def get_mtb(zielbreite, ziellaenge):
    """Berechnung der Messtischblattnummer

    Ausgehend vom O-Punkt (virutelle Karte mit der Bezeichnung 0502
    weil für Zeile 0519, 0520, 0521 die nördlichsten MTB existieren.
    Für die Berechnung müssen die Opensteetmap-Koordinaten in Bogen-
    maß umgerechent werden. Aus dem Kartenmaß für die Höhe (6 Grad)
    und der Breite (10 Grad) kann dann die Kartennummer errechnet
    werden.                                 

    Die Grenzen, ob eine Karte mit der errechneten Nummer existiert
    oder es eine virtuelle MTB-Nummer ist, wird nicht geprüft.

    Ob die errechnite Nummer korrekt ist, kann auf der folgenden
    Websiten nachgeprüft werden:            

    - http://gk.historic.place/tools/selectbbox.htm
    - https://moses-mendelssohn-institut.de/TK25  
    """
    # Berechnung der Zeilennummer

    zielbreite = float(str(zielbreite).replace(",", "."))
    ziellaenge = float(str(ziellaenge).replace(",", "."))

    startbreite = 55.49839  # Quadrat liegt im Meer Höhe Esbjerg (Dänemark)
    startlaenge = 6.0  # 5.99931  # und markiert den 0-Punkt für die Berechnungen
    startnummer = 5  # Zeile im Kachelsystem
    zielstunden, zielnach = (int(zielbreite // 1), zielbreite % 1)
    zielminsec = zielnach * 60
    zielminuten = int(zielminsec // 1)
    zielsekunden = (zielminsec % 1) * 60
    startvor, startnach = (int(startbreite // 1), startbreite % 1)
    startminsec = startnach * 60
    startminuten = int(startminsec // 1)
    startsekunden = (startminsec % 1) * 60
    diffstunden = startvor - zielstunden
    diffminuten = startminuten - zielminuten
    diffgesamt = diffstunden * 60 + diffminuten
    part1 = int(startnummer + diffgesamt / 6)

    # Berechnung der Spaltennummer

    zielstunden, zielnach = (int(ziellaenge // 1), ziellaenge % 1)
    zielminsec = zielnach * 60
    zielminuten = int(zielminsec // 1)
    zielsekunden = (zielminsec % 1) * 60
    startnummer = 2  # Spalte im Kachelsystem

    startvor, startnach = (int(startlaenge // 1), startlaenge % 1)
    startminsec = startnach * 60
    startminuten = int(startminsec // 1)
    startsekunden = (startminsec % 1) * 60
    diffstunden = abs(startvor - zielstunden)

    diffminuten = abs(abs(startminuten) + abs(zielminuten))
    diffgesamt = abs(diffstunden) * 60 + abs(diffminuten)
    part2 = int(startnummer + diffgesamt / 10)

    return f"{part1:02d}{part2:02d}"


if __name__ == '__main__':

    koordinaten = [
        (52.43257, 9.74487, 'Langenhagen'),
        # Id: 4940 mtb: 6707
        (49.20753, 6.84002, 'Regionalverband Saarbrücken | Großro'),
        (51.3324, 12.07906, 'Leuna'),  # Id : 4934 mtb: 4638
        (50.71869, 7.11366, 'Kessenich | Bonn'),  # Id: 4947 mtb: 5208
        (52.05791, 13.18969, 'Kolzenburg'),  # id 4948 mtb: 3945
        (52.04057, 13.49549, 'Baruth'),  # id: 4949 mtb: 3946
        # ID: 4950 mtb: 4632
        (51.36304, 11.11348, 'Kyffhäuserkreis | Bad Frankenhausen'),
        (51.57738, 13.99804, 'Großräschen'),   # Großräschen ID: 4951 mtb: 4450
        (52.95927, 9.9396, 'Visselhövede'),      # Visselhövede
        (52.37225, 12.96936, 'Werder'),        # Werder mtb: 3643
        (52.3874, 13.40296, 'Lichtenrade'),    # Lichtenrade ID: 4945 mtb: 3646
        (52.83862, 13.81361, 'Eberswalde'),    # Eberswalde ID: 4946 mtb: 3149
    ]

    for row in koordinaten:

        zielbreite, ziellaenge, ort = row
        print(get_mtb(zielbreite, ziellaenge), ort)
