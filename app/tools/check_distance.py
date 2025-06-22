"""
Function to  get coordinates an address (street, cty, housnumber)
with Nominatim API.
Could also be testet in a browser:

https://nominatim.openstreetmap.org/search?\
   q=Schmerberger+Weg+Caputh&format=json&addressdetails=1&limit=1
https://nominatim.openstreetmap.org/search?\n
   q=Dorfstraße+Fichtwald+04936+8&format=json&addressdetails=1&limit=3
"""

import requests
from geopy.distance import geodesic
import time


def get_coordinates_from_address(street, city, plz=None, housenumber=None):
    # Nominatim API URL
    url = "https://nominatim.openstreetmap.org/search"

    # composit the address
    if housenumber:
        full_address = f"{housenumber} {street}, {plz}, {city}, Germany"
    else:
        full_address = f"{street}, {city}, Germany"

    # setup parameters
    params = {
        'q': full_address,        # Detailierte Adresse
        'format': 'json',         # result as JSON
        'addressdetails': 1,
        'limit': 1                # first result if more than one
    }
    # Header with  User-Agent für Nominatim API (mandatory)
    # change URL to your setup
    headers = {
        'User-Agent': 'Python/GeocodingScript (https://example.com)'
    }

    # send request to  Nominatim API
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data:
            # get coordinates
            latitude = float(data[0]["lat"])
            longitude = float(data[0]["lon"])
            return latitude, longitude
        else:
            print("Address not found!")
            return None
    else:
        print("Erreor on request!")
        return None


def calculate_distance(coord1, coord2):
    return geodesic(coord1, coord2).km


if __name__ == '__main__':
    from fundorte_data import adresses
    with open("results.txt", "w") as fh:
        for ort in adresses:
            time.sleep(1.0)
            coord1 = get_coordinates_from_address(
                ort["street"],
                ort["city"],
                ort["plz"],
                ort["housenumber"])
            coord2 = ort['marker']

            if coord1 and coord2:
                distance = calculate_distance(coord1, coord2)
                fh.write(f"{distance:.2f}.km, id={ort['id']} , \
                between Marker and address {ort['city']}, \
                {ort['street']}, {ort['housenumber']}\n")
            else:
                fh.write(f"Error, meldeid={ort['id']}, address \
                {ort['city']}, {ort['street']}, {ort['housenumber']}\n")
            fh.flush()
