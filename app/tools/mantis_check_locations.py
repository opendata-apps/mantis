import requests
import re

overpass_url = "http://overpass-api.de/api/interpreter"


def check_location(fundort):
    results = []
    lat, lon, ort, id = fundort
    weiter = True
    dist = 200
    ort = re.findall(r"[\w']+", ort)[0]
    place_names = set()
    try:
        while weiter:
            overpass_query = f'''
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
            '''
            response = requests.get(overpass_url,
                                    params={'data': overpass_query})
            data = response.json()
            for element in data['elements']:
                if 'tags' in element and 'name' in element['tags']:
                    place_names.add(element['tags']['name'])
            name_set = ', '.join(place_names)
            orte = re.findall(r"[\w']+", name_set)

            # Extrahieren der Ortsnamen

            if ort in orte:
                results.append((f"{dist}, {ort}, {id}, OK\n"))
                weiter = False
                print((f"{dist}, {ort}, {id}, OK\n"))
            elif dist < 5000:
                dist += 200
            else:
                dist += 5000

            if dist == 50000:
                results.append((f"{dist}, {ort}, {id}, <-- Prüfen!\n"))
                weiter = False
    except Exception as e:
        results.append((f" {dist},  {ort}, {id},  <-- Abbruch!\n"))
        print(e)

    return results


if __name__ == "__main__":

    locations = [
        (52.38948, 12.70295, "Schenkenberg", 1908),
    ]
    # locations = [
    #    # (51.94966,14.06826,"Caminchen",854),
    #    # (52.37982, 13.2579, "Teltow", 378),
    #    (51.72459, 14.63499,"Forst (Lausitz)", 166)
    # (52.00539,14.5071,"Schenkendöbern",716),
    # ]
    with open('ergebnis', 'w') as fh:
        for fundort in locations:
            if fundort[2] != "Berlin":
                fh.write("".join(check_location(fundort=fundort)))
