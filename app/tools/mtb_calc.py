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

def get_mtb(zielbreite, ziellaenge):
    "Berechnung der Messtischblattnummer"
    
    # Berechnung der Zeilennummer
    
    startbreite = 55.87688 #55.49839 # Quadrat liegt im Meer Höhe Esbjerg (Dänemark)
    startlaenge = 6.0 #5.99931  # und markiert den 0-Punkt für die Berechnungen
    startnummer = 1 # Zeile im Kachelsystem 
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
    startnummer = 2 # Spalte im Kachelsystem
                                            
    startvor, startnach = (int(startlaenge // 1), startlaenge % 1)
    startminsec = startnach * 60            
    startminuten = int(startminsec // 1)    
    startsekunden = (startminsec % 1) * 60  
    diffstunden = abs(startvor - zielstunden)
                                            
    diffminuten = abs(abs(startminuten) + abs(zielminuten))
    diffgesamt = abs(diffstunden) * 60 + abs(diffminuten)
    part2 = int(startnummer + diffgesamt / 10)

    return f"{part1:02d}{part2:02d}"        

def pointInRect(point):
    "Test, ob Punkt im definierten Rechteck liegt"
    
    rect = (47.0,6.0,9.0, 18.0)
    x1, y1, w, h = rect
    x2, y2 = x1+w, y1+h
    x, y = point
    if (x1 < x and x < x2):
        if (y1 < y and y < y2):
            return True
        else:
            return False
    return False


if __name__ == '__main__':

    koordinaten = [
        (47.391911055382316, 8.521261525400504, 'Zürich'),
        (46.06344, 13.22602, 'Udine'),
        (52.07820, 5.12657, 'Utrecht'),
        (52.43257, 9.74487, 'Langenhagen'),
        (49.20753, 6.84002, 'Regionalverband Saarbrücken | Großro'),
        (51.3324, 12.07906, 'Leuna'),              # 4638
        (50.71869, 7.11366, 'Kessenich | Bonn'),   # 5208
        (52.05791, 13.18969, 'Kolzenburg'),        # 3945
        (52.04057, 13.49549, 'Baruth'),            # 3946
        (51.36304, 11.11348, 'Kyffhäuserkreis | Bad Frankenhausen'),
        (51.57738, 13.99804, 'Großräschen'),       # 4450
        (52.95927, 9.9396, 'Visselhövede'),        # 
        (52.37225, 12.96936, 'Werder'),            # 3643
        (52.3874, 13.40296, 'Lichtenrade'),        # 3646
        (52.83862, 13.81361, 'Eberswalde'),        # 3149
        (53.116606,20.36675,'Mława'),
        (54.144753, 19.410705, 'Elbing'),          # 1882
        (55.710785,21.131742, 'Klaipeda, Litauen'),# 0292
        (55.131794,23.350251, 'Girkai, Litauen'),  # falsch berechnet
    ]


    for row in koordinaten:
        zielbreite, ziellaenge, ort = row
        print(get_mtb(zielbreite, ziellaenge), ort,
              pointInRect((zielbreite, ziellaenge)))
                                            
