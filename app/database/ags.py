"""
Amtlicher Gemeindeschlüssel (AGS) reference data.

Single source of truth for German administrative division codes and names.
Names use the official Destatis short forms.

Source: Statistisches Bundesamt (Destatis)
https://www.destatis.de/DE/Themen/Laender-Regionen/Regionales/Gemeindeverzeichnis/Glossar/bundeslaender.html

Structure: Land (2) + Regierungsbezirk (1) + Kreis (2) + Gemeinde (3)
"""

# 2-digit state codes → Destatis official names
BUNDESLAENDER: dict[str, str] = {
    "01": "Schleswig-Holstein",
    "02": "Hamburg",
    "03": "Niedersachsen",
    "04": "Bremen",
    "05": "Nordrhein-Westfalen",
    "06": "Hessen",
    "07": "Rheinland-Pfalz",
    "08": "Baden-Württemberg",
    "09": "Bayern",
    "10": "Saarland",
    "11": "Berlin",
    "12": "Brandenburg",
    "13": "Mecklenburg-Vorpommern",
    "14": "Sachsen",
    "15": "Sachsen-Anhalt",
    "16": "Thüringen",
}

# 8-digit Berlin district codes (Stadtbezirke)
BERLIN_BEZIRKE: dict[str, str] = {
    "11000000": "Berlin (allgemein)",
    "11000001": "Mitte",
    "11000002": "Friedrichshain-Kreuzberg",
    "11000003": "Pankow",
    "11000004": "Charlottenburg-Wilmersdorf",
    "11000005": "Spandau",
    "11000006": "Steglitz-Zehlendorf",
    "11000007": "Tempelhof-Schöneberg",
    "11000008": "Neukölln",
    "11000009": "Treptow-Köpenick",
    "11000010": "Marzahn-Hellersdorf",
    "11000011": "Lichtenberg",
    "11000012": "Reinickendorf",
}

# 5-digit Brandenburg district codes (Landkreise + kreisfreie Städte)
BRANDENBURG_LANDKREISE: dict[str, str] = {
    "12060": "Landkreis Barnim",
    "12061": "Landkreis Dahme-Spreewald",
    "12062": "Landkreis Elbe-Elster",
    "12063": "Landkreis Havelland",
    "12064": "Landkreis Märkisch-Oderland",
    "12065": "Landkreis Oberhavel",
    "12066": "Landkreis Oberspreewald-Lausitz",
    "12067": "Landkreis Oder-Spree",
    "12068": "Landkreis Ostprignitz-Ruppin",
    "12069": "Landkreis Potsdam-Mittelmark",
    "12070": "Landkreis Prignitz",
    "12071": "Landkreis Spree-Neiße",
    "12072": "Landkreis Teltow-Fläming",
    "12073": "Landkreis Uckermark",
    "12051": "Brandenburg an der Havel",
    "12052": "Cottbus",
    "12053": "Frankfurt (Oder)",
    "12054": "Potsdam",
}


def build_gesamt_template() -> dict[str, list]:
    """Build the initial result structure for the hierarchical summary table.

    Returns a dict keyed by AGS code with value:
    [state_name, district_name, amt_name, count, sub_rows]
    """
    result: dict[str, list] = {}
    for code, name in BUNDESLAENDER.items():
        result[code] = [name, "", "", 0, []]
    for code, name in BRANDENBURG_LANDKREISE.items():
        result[code] = ["", name, "", 0, []]
    return result
