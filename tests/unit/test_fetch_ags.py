"""Unit tests for pure helper functions in app/tools/fetch_ags.py.

Tests the data transformation, merging, and file I/O functions that process
administrative area (AGS) data from WFS services. No HTTP calls needed —
these all operate on plain dicts and files.
"""

import pytest

from app.tools.fetch_ags import (
    build_kreise_lookup,
    load_kreise_lookup,
    merge_gemeinden_with_berlin,
    save_fallback,
    save_kreise_lookup,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def bkg_feature():
    """A single BKG VG5000 Gemeinde feature as returned by the WFS."""
    return {
        "type": "Feature",
        "properties": {
            "ags": "12054000",
            "gen": "Potsdam",
            "bez": "Kreisfreie Stadt",
            "extra_field": "ignored",
        },
        "geometry": {"type": "Point", "coordinates": [13.06, 52.39]},
    }


@pytest.fixture
def berlin_feature():
    """A single Berlin ALKIS Bezirk feature as returned by the WFS."""
    return {
        "type": "Feature",
        "properties": {
            "name": "11000001",
            "namgem": "Mitte",
            "schluessel": "01",
        },
        "geometry": {"type": "Polygon", "coordinates": [[[13.3, 52.5]]]},
    }


@pytest.fixture
def gemeinden_data(bkg_feature):
    """A minimal FeatureCollection including one Berlin whole-city entry."""
    berlin_whole = {
        "type": "Feature",
        "properties": {"ags": "11000000", "gen": "Berlin"},
        "geometry": {"type": "Polygon", "coordinates": [[[13.4, 52.5]]]},
    }
    return {"type": "FeatureCollection", "features": [bkg_feature, berlin_whole]}


@pytest.fixture
def kreise_data():
    """A minimal Kreise FeatureCollection with different Bezirk types."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "properties": {
                    "ags": "12054",
                    "gen": "Potsdam",
                    "bez": "Kreisfreie Stadt",
                }
            },
            {
                "properties": {
                    "ags": "12060",
                    "gen": "Barnim",
                    "bez": "Landkreis",
                }
            },
            {
                "properties": {
                    "ags": "08111",
                    "gen": "Stuttgart",
                    "bez": "Stadtkreis",
                }
            },
        ],
    }


# ---------------------------------------------------------------------------
# build_kreise_lookup
# ---------------------------------------------------------------------------


def test_kreise_lookup_prefixes_counties_but_not_cities(kreise_data):
    lookup = build_kreise_lookup(kreise_data)
    assert lookup == {
        "12054": "Potsdam",
        "12060": "Landkreis Barnim",
        "08111": "Stuttgart",
    }


def test_kreise_lookup_empty_input():
    assert build_kreise_lookup({"features": []}) == {}


# ---------------------------------------------------------------------------
# merge_gemeinden_with_berlin
# ---------------------------------------------------------------------------


def test_merge_replaces_berlin_city_with_normalized_districts(
    gemeinden_data, berlin_feature
):
    merged = merge_gemeinden_with_berlin(gemeinden_data, [berlin_feature])

    assert merged == {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"AGS": "12054000", "GEN": "Potsdam"},
                "geometry": {"type": "Point", "coordinates": [13.06, 52.39]},
            },
            {
                "type": "Feature",
                "properties": {"AGS": "11000001", "GEN": "Mitte"},
                "geometry": {"type": "Polygon", "coordinates": [[[13.3, 52.5]]]},
            },
        ],
    }


# ---------------------------------------------------------------------------
# save_fallback
# ---------------------------------------------------------------------------


def test_save_fallback_writes_valid_json(tmp_path):
    import json

    data = {"type": "FeatureCollection", "features": [{"id": 1}]}
    path = tmp_path / "sub" / "fallback.json"
    save_fallback(data, path)

    assert path.exists()
    with open(path, encoding="utf-8") as f:
        assert json.load(f) == data


def test_save_fallback_creates_parent_dirs(tmp_path):
    path = tmp_path / "a" / "b" / "c" / "data.json"
    save_fallback({"features": []}, path)
    assert path.exists()


# ---------------------------------------------------------------------------
# save_kreise_lookup / load_kreise_lookup
# ---------------------------------------------------------------------------


def test_save_and_load_kreise_roundtrip(tmp_path):
    lookup = {"12054": "Potsdam", "12060": "Landkreis Barnim"}
    path = tmp_path / "kreise.json"

    save_kreise_lookup(lookup, path)
    loaded = load_kreise_lookup(path)

    assert loaded == lookup


def test_save_kreise_creates_parent_dirs(tmp_path):
    path = tmp_path / "x" / "y" / "kreise.json"
    save_kreise_lookup({}, path)
    assert path.exists()
