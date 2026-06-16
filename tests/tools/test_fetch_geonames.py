from app.tools.fetch_ags import parse_geonames_featurecollection

_TYPE_BASE = "http://inspire.ec.europa.eu/codelist/NamedPlaceTypeValue"


def _feature(name, type_suffix, coords):
    """Build a GN250-INSPIRE-shaped feature (nested name, href type)."""
    return {
        "properties": {
            "name": {
                "GeographicalName": {"spelling": {"SpellingOfName": {"text": name}}}
            },
            "type": {"href": f"{_TYPE_BASE}/{type_suffix}"},
        },
        "geometry": {"type": "Point", "coordinates": coords} if coords else None,
    }


_FC = {
    "features": [
        _feature("Schadewitz", "populatedPlace", [13.52, 51.58]),
        _feature("Blauer See", "landform", [13.5, 51.6]),  # non-settlement, dropped
        _feature("Nowhere", "populatedPlace", None),  # missing geometry, dropped
    ]
}


def test_parse_keeps_only_populated_places_with_points():
    rows = parse_geonames_featurecollection(_FC)
    assert len(rows) == 1
    r = rows[0]
    assert r["name"] == "Schadewitz"
    assert r["longitude"] == 13.52 and r["latitude"] == 51.58
    # The INSPIRE-harmonized GN250 view exposes no administrative keys.
    assert r["ags"] is None
    assert r["kreis"] is None
