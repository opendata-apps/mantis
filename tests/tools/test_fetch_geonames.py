from app.tools.fetch_ags import parse_geonames_featurecollection

_FC = {
    "features": [
        {
            "properties": {
                "name": "Schadewitz",
                "type": "populatedPlace",
                "ags": "12062264",
                "kreis": "Elbe-Elster",
            },
            "geometry": {"type": "Point", "coordinates": [13.52, 51.58]},
        },
        {  # non-settlement, must be dropped
            "properties": {"name": "Blauer See", "type": "landform"},
            "geometry": {"type": "Point", "coordinates": [13.5, 51.6]},
        },
        {  # missing geometry, must be dropped
            "properties": {"name": "Nowhere", "type": "populatedPlace"},
            "geometry": None,
        },
    ]
}


def test_parse_keeps_only_populated_places_with_points():
    rows = parse_geonames_featurecollection(_FC)
    assert len(rows) == 1
    r = rows[0]
    assert r["name"] == "Schadewitz"
    assert r["longitude"] == 13.52 and r["latitude"] == 51.58
    assert r["ags"] == 12062264
    assert r["kreis"] == "Elbe-Elster"
