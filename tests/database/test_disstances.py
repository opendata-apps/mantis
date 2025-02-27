import time
import requests
from geopy.distance import geodesic
from app.tools.check_distance import get_coordinates_from_address
from app.tools.check_distance import  calculate_distance

ort = {
        "id": 11,
        "plz": "14548",
        "city": "Caputh",
        "street": "Schmerberger Weg 92a",
        "housenumber": None,
        "marker": [
            "51.464414",
            "13.540649"
        ]
    }

def test_distance_caputh(session):
    # Beispiel-Test, um zu prüfen, ob eine Tabelle existiert

    coord1 = get_coordinates_from_address(
        ort["street"],
        ort["city"],
        ort["plz"],
        ort["housenumber"])
    coord2 = ort['marker']
    if coord1 and coord2:
        distance = calculate_distance(coord1, coord2)
    assert distance > 10.0
