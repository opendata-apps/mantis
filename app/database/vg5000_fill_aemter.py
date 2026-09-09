"""Tabelle  'aemter' mit Datensätzen
aus vg5000_gem füllen
"""

import json

from sqlalchemy import select

from app.database.aemter_koordinaten import TblAemterCoordinaten


def import_aemter_data(session, jsondata):
    data = json.loads(jsondata)

    # One query for the whole set, not one per municipality. entrypoint.sh runs
    # the seed on every container start, where all ~11k rows already exist, and
    # asking for them one at a time cost eight of the fourteen seconds a deploy
    # was down.
    known = set(session.scalars(select(TblAemterCoordinaten.ags)))

    for row in data["features"]:
        ags = int(row["properties"]["AGS"])
        if ags in known:
            continue

        session.add(
            TblAemterCoordinaten(
                ags=ags, gen=row["properties"]["GEN"], properties=row["geometry"]
            )
        )
        # The file may name the same area twice; the old per-row lookup caught
        # that through the session, this has to remember it.
        known.add(ags)

    session.commit()
