"""Tabelle  'aemter' mit Datensätzen
aus vg5000_gem füllen
"""

import json

from app.database.aemter_koordinaten import TblAemterCoordinaten


def import_aemter_data(session, jsondata):
    data = json.loads(jsondata)

    for row in data["features"]:
        ags = int(row["properties"]["AGS"])
        gen = row["properties"]["GEN"]

        existing = session.get(TblAemterCoordinaten, ags)
        if existing:
            continue

        area = TblAemterCoordinaten(ags=ags, gen=gen, properties=row["geometry"])
        session.add(area)

    session.commit()
