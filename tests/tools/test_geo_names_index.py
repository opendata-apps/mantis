from app.tools.geo_names import GeoNamesIndex

# (name, ags, kreis, lon, lat)
_PLACES = [
    ("Schadewitz", 12062264, "Elbe-Elster", 13.52, 51.58),
    ("Cottbus", 12052000, "Cottbus", 14.33, 51.76),
]


def test_nearest_returns_closest_place_and_distance():
    idx = GeoNamesIndex.from_rows(_PLACES)
    place = idx.nearest((13.521, 51.581))  # next to Schadewitz
    assert place.name == "Schadewitz"
    assert place.ags == 12062264
    assert place.distance_m < 200


def test_nearest_on_empty_index_returns_none():
    idx = GeoNamesIndex.from_rows([])
    assert idx.nearest((13.0, 52.0)) is None
