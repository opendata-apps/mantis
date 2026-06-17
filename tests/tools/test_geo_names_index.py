import math

from app.tools.geo_names import _MIN_M_PER_DEG, GeoNamesIndex

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


def test_nearest_places_returns_all_in_radius_sorted():
    # Two places ~1.5 km apart; a pin near the first must surface BOTH (nearest
    # first) so a matching name farther out is not shadowed by a closer one.
    rows = [
        ("Olympisches Dorf", None, "Havelland", 13.0050, 52.5260),
        ("Elstal", None, "Havelland", 13.0250, 52.5260),
    ]
    idx = GeoNamesIndex.from_rows(rows)
    found = idx.nearest_places((13.0040, 52.5260), radius_m=3000.0)
    assert [p.name for p in found] == ["Olympisches Dorf", "Elstal"]
    assert found[0].distance_m < found[1].distance_m


def test_nearest_places_falls_back_to_absolute_nearest():
    idx = GeoNamesIndex.from_rows(_PLACES)
    # Pin far from both places (>5 km): radius is empty, fall back to nearest one.
    found = idx.nearest_places((13.0, 52.0), radius_m=1000.0)
    assert len(found) == 1


def test_nearest_places_on_empty_index_returns_empty():
    idx = GeoNamesIndex.from_rows([])
    assert idx.nearest_places((13.0, 52.0)) == []


def test_prefilter_constant_covers_german_latitude_span():
    # The metres->degrees dwithin prefilter is only over-inclusive (never drops a
    # true in-range place) while 1 deg of longitude stays >= _MIN_M_PER_DEG. Germany
    # reaches ~55.1 deg N, so assert the constant holds there with margin.
    m_per_deg_lon_at_north = 111320 * math.cos(math.radians(55.1))
    assert m_per_deg_lon_at_north >= _MIN_M_PER_DEG


def test_nearest_places_finds_in_range_point_at_northern_extreme():
    # Two places ~2.9 km apart at Germany's northern edge (the binding latitude for
    # the prefilter): both must surface within a 3 km radius.
    rows = [
        ("Aventoft", None, "Nordfriesland", 8.8000, 55.0500),
        ("Rosenkranz", None, "Nordfriesland", 8.8455, 55.0500),
    ]
    idx = GeoNamesIndex.from_rows(rows)
    found = idx.nearest_places((8.7990, 55.0500), radius_m=3000.0)
    assert {p.name for p in found} == {"Aventoft", "Rosenkranz"}
