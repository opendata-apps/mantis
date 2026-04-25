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
    """Berechnung der Messtischblattnummer.

    Uses full decimal-degree precision to avoid off-by-one errors
    at tile boundaries. Each TK25 sheet covers 6' latitude (row)
    and 10' longitude (column).
    """
    startbreite = 55.87688  # Grid origin latitude (north edge of row 1)
    startlaenge = 6.0  # Grid origin longitude (west edge of column 2)

    row = int(1 + ((startbreite - zielbreite) * 60) / 6)
    col = int(2 + ((ziellaenge - startlaenge) * 60) / 10)

    return f"{row:02d}{col:02d}"


def point_in_rect(point):
    """Check if a (lat, lon) point is within the Germany bounding box.

    Western bound is 5.83 (not 6.0) to include the Selfkant exclave (NRW),
    home of TK25 sheet 4901 at ~5°55' E.
    """
    lat, lon = point
    return 47.0 < lat < 56.0 and 5.83 < lon < 24.0


if __name__ == "__main__":
    koordinaten = [
        (47.391911055382316, 8.521261525400504, "Zürich"),
        (46.06344, 13.22602, "Udine"),
        (52.07820, 5.12657, "Utrecht"),
        (52.43257, 9.74487, "Langenhagen"),
        (49.20753, 6.84002, "Regionalverband Saarbrücken | Großro"),
        (51.3324, 12.07906, "Leuna"),  # 4638
        (50.71869, 7.11366, "Kessenich | Bonn"),  # 5208
        (52.05791, 13.18969, "Kolzenburg"),  # 3945
        (52.04057, 13.49549, "Baruth"),  # 3946
        (51.36304, 11.11348, "Kyffhäuserkreis | Bad Frankenhausen"),
        (51.57738, 13.99804, "Großräschen"),  # 4349
        (52.95927, 9.9396, "Visselhövede"),
        (52.37225, 12.96936, "Werder"),  # 3643
        (52.3874, 13.40296, "Lichtenrade"),  # 3546
        (52.83862, 13.81361, "Eberswalde"),  # 3148
        (53.116606, 20.36675, "Mława"),
        (54.144753, 19.410705, "Elbing"),  # 1882
        (55.710785, 21.131742, "Klaipeda, Litauen"),  # 0292
        (55.131794, 23.350251, "Girkai, Litauen"),  # falsch berechnet
    ]

    for row in koordinaten:
        zielbreite, ziellaenge, ort = row
        print(
            get_mtb(zielbreite, ziellaenge),
            ort,
            point_in_rect((zielbreite, ziellaenge)),
        )
