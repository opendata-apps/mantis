import requests
import re
import argparse

overpass_url = "https://overpass-api.de/api/interpreter"


def check_location(fundort):
    results = []
    lat, lon, ort, fundort_id = fundort
    weiter = True
    dist = 200
    ort = re.findall(r"[\w']+", ort)[0]
    place_names = set()
    try:
        while weiter:
            overpass_query = f"""
                [out:json];
                (
                  node["place"~"village|town|city|hamlet|suburb"](around:{dist},{lat},{lon});
                  way["place"~"village|town|city|hamlet|suburb"](around:{dist},{lat},{lon});
                  relation["place"~"village|town|city|hamlet|suburb"](around:{dist},{lat},{lon});
                );
                out body;
                >;
                out skel qt;

                for (t["name"]) {{
                  out body;
                }}
            """
            response = requests.get(
                overpass_url, params={"data": overpass_query}, timeout=30
            )
            data = response.json()
            for element in data["elements"]:
                if "tags" in element and "name" in element["tags"]:
                    place_names.add(element["tags"]["name"])
            name_set = ", ".join(place_names)
            orte = re.findall(r"[\w']+", name_set)

            # Extrahieren der Ortsnamen

            if ort in orte:
                results.append(f"{dist}, {ort}, {fundort_id}, OK\n")
                weiter = False
                print(f"{dist}, {ort}, {fundort_id}, OK\n")
            elif dist < 5000:
                dist += 200
            else:
                dist += 5000

            if dist == 50000:
                results.append(f"{dist}, {ort}, {fundort_id}, <-- Prüfen!\n")
                weiter = False
    except Exception as e:
        results.append(f" {dist},  {ort}, {fundort_id},  <-- Abbruch!\n")
        print(e)

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check a location with Overpass.")
    parser.add_argument("latitude", type=float)
    parser.add_argument("longitude", type=float)
    parser.add_argument("place")
    parser.add_argument("record_id", type=int)
    args = parser.parse_args()
    locations = [(args.latitude, args.longitude, args.place, args.record_id)]
    with open("ergebnis", "w") as fh:
        for fundort in locations:
            if fundort[2] != "Berlin":
                fh.write("".join(check_location(fundort=fundort)))
