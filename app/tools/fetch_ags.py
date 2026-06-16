"""
Fetch administrative area (AGS) data from official WFS services.

Sources:
- BKG (Bundesamt für Kartographie und Geodäsie): VG5000 Gemeinden + Kreise
  https://sgx.geodatenzentrum.de/wfs_vg5000_0101
- Berlin Geoportal: ALKIS Bezirke (12 city districts)
  https://gdi.berlin.de/services/wfs/alkis_bezirke

License: Datenlizenz Deutschland – Namensnennung 2.0 (dl-de/by-2-0)
Attribution: © GeoBasis-DE / BKG, © Geoportal Berlin / ALKIS Berlin Bezirke
"""

import json
import logging
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

BKG_WFS_BASE = "https://sgx.geodatenzentrum.de/wfs_vg5000_0101"
BERLIN_WFS_BASE = "https://gdi.berlin.de/services/wfs/alkis_bezirke"

# Berlin whole-city AGS — replaced by 12 Bezirke from ALKIS
BERLIN_WHOLE_CITY_AGS = "11000000"

REQUEST_TIMEOUT = 30  # seconds


def _wfs_get_feature(base_url, typename, *, srs="EPSG:4326", extra_params=None):
    """Fetch all features from a WFS endpoint as GeoJSON."""
    params = {
        "service": "wfs",
        "version": "2.0.0",
        "request": "GetFeature",
        "typenames": typename,
        "outputFormat": "application/json",
        "srsName": srs,
    }
    if extra_params:
        params.update(extra_params)

    resp = requests.get(base_url, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


GN250_WFS_BASE = "https://sgx.geodatenzentrum.de/wfs_gn250_inspire"

# GN250 NamedPlace type values (the href suffix) worth grading against.
_GEONAME_SETTLEMENT_TYPES = {"populatedPlace"}

# Server-side page size; the INSPIRE endpoint caps a single GetFeature response
# and does not report numberMatched, so we page on startIndex until a short page.
GN250_PAGE_SIZE = 10000


def _geoname_text(name_prop):
    """Extract the spelling text from an INSPIRE GeographicalName property.

    The property nests as name.GeographicalName.spelling.SpellingOfName.text;
    either of the inner objects may be a list (a place with several names).
    """
    if isinstance(name_prop, list):
        name_prop = name_prop[0] if name_prop else None
    if not isinstance(name_prop, dict):
        return None
    gn = name_prop.get("GeographicalName") or {}
    spelling = gn.get("spelling")
    if isinstance(spelling, list):
        spelling = spelling[0] if spelling else None
    son = (spelling or {}).get("SpellingOfName") or {}
    text = son.get("text")
    return text.strip() if isinstance(text, str) and text.strip() else None


def parse_geonames_featurecollection(fc):
    """Normalize a GN250 INSPIRE GeoJSON FeatureCollection to geo_names rows.

    Keeps only populated places with a point geometry. The INSPIRE-harmonized
    view exposes no administrative keys, so ags/kreis are always None.
    """
    rows = []
    for feat in fc.get("features", []):
        props = feat.get("properties") or {}
        href = (props.get("type") or {}).get("href", "")
        if href.rsplit("/", 1)[-1] not in _GEONAME_SETTLEMENT_TYPES:
            continue
        geom = feat.get("geometry") or {}
        coords = geom.get("coordinates") if geom.get("type") == "Point" else None
        if not coords or len(coords) < 2:
            continue
        name = _geoname_text(props.get("name"))
        if not name:
            continue
        rows.append(
            {
                "name": name,
                "longitude": float(coords[0]),
                "latitude": float(coords[1]),
                "ags": None,
                "kreis": None,
            }
        )
    return rows


def fetch_geonames():
    """Fetch all GN250 populated places from the BKG INSPIRE WFS as GeoJSON.

    Pages on startIndex until a short page; GN250 advertises
    'application/geo+json' (it rejects 'application/json').
    """
    logger.info("Fetching GN250 named places from BKG WFS...")
    rows = []
    start = 0
    while True:
        data = _wfs_get_feature(
            GN250_WFS_BASE,
            "gn:NamedPlace",
            extra_params={
                "outputFormat": "application/geo+json",
                "count": GN250_PAGE_SIZE,
                "startIndex": start,
            },
        )
        feats = data.get("features", [])
        rows.extend(parse_geonames_featurecollection(data))
        if len(feats) < GN250_PAGE_SIZE:
            break
        start += GN250_PAGE_SIZE
    logger.info(f"Fetched {len(rows)} GN250 populated places")
    return rows


def fetch_gemeinden():
    """Fetch all Gemeinden (municipalities) from BKG VG5000 WFS.

    Returns a FeatureCollection dict with ~10,949 features.
    """
    logger.info("Fetching Gemeinden from BKG VG5000 WFS...")
    data = _wfs_get_feature(BKG_WFS_BASE, "vg5000_0101:vg5000_gem")
    count = data.get("numberReturned", len(data.get("features", [])))
    logger.info(f"Fetched {count} Gemeinden from BKG")
    return data


def fetch_kreise():
    """Fetch all Kreise (counties) from BKG VG5000 WFS.

    Returns a FeatureCollection dict with ~400 features.
    """
    logger.info("Fetching Kreise from BKG VG5000 WFS...")
    data = _wfs_get_feature(BKG_WFS_BASE, "vg5000_0101:vg5000_krs")
    count = data.get("numberReturned", len(data.get("features", [])))
    logger.info(f"Fetched {count} Kreise from BKG")
    return data


def fetch_berlin_bezirke():
    """Fetch Berlin Bezirke (12 city districts) from Berlin ALKIS WFS.

    Returns a list of GeoJSON features.
    """
    logger.info("Fetching Berlin Bezirke from ALKIS WFS...")
    data = _wfs_get_feature(BERLIN_WFS_BASE, "alkis_bezirke:bezirksgrenzen")
    features = data.get("features", [])
    logger.info(f"Fetched {len(features)} Berlin Bezirke")
    return features


def _normalize_bkg_feature(feature):
    """Strip a BKG feature down to AGS, GEN, and geometry only."""
    props = feature["properties"]
    return {
        "type": "Feature",
        "properties": {
            "AGS": props["ags"],
            "GEN": props["gen"],
        },
        "geometry": feature["geometry"],
    }


def _normalize_berlin_feature(feature):
    """Normalize a Berlin ALKIS feature to match our schema."""
    props = feature["properties"]
    return {
        "type": "Feature",
        "properties": {
            "AGS": props["name"],  # "11000001"
            "GEN": props["namgem"],  # "Mitte"
        },
        "geometry": feature["geometry"],
    }


def build_kreise_lookup(kreise_data):
    """Build a {ags_5_digit: "Kreis Name"} dict from WFS Kreise data.

    For kreisfreie Städte, stores just the city name.
    For Landkreise, stores "Landkreis Name" etc.
    """
    lookup = {}
    for feature in kreise_data.get("features", []):
        props = feature["properties"]
        ags5 = props["ags"]
        bez = props["bez"]
        gen = props["gen"]
        # Kreisfreie Städte: just the name. Others: "Bezeichnung Name"
        if bez in ("Kreisfreie Stadt", "Stadtkreis"):
            lookup[ags5] = gen
        else:
            lookup[ags5] = f"{bez} {gen}"
    return lookup


def merge_gemeinden_with_berlin(gemeinden_data, berlin_features):
    """Replace Berlin whole-city polygon with 12 Bezirk polygons.

    - Removes the single Berlin feature (AGS 11000000) from VG5000
    - Adds 12 normalized Berlin Bezirk features from ALKIS
    - Normalizes all properties to {AGS, GEN}
    """
    merged = []

    for feature in gemeinden_data.get("features", []):
        ags = feature["properties"]["ags"]
        if ags == BERLIN_WHOLE_CITY_AGS:
            continue  # skip Berlin whole-city, replaced by Bezirke
        merged.append(_normalize_bkg_feature(feature))

    for feature in berlin_features:
        merged.append(_normalize_berlin_feature(feature))

    logger.info(
        f"Merged: {len(merged)} features "
        f"({len(gemeinden_data.get('features', [])) - 1} Gemeinden + "
        f"{len(berlin_features)} Berlin Bezirke)"
    )

    return {
        "type": "FeatureCollection",
        "features": merged,
    }


def save_fallback(data, path):
    """Save merged GeoJSON to a fallback file with compact formatting."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    size_mb = path.stat().st_size / (1024 * 1024)
    logger.info(f"Saved fallback to {path} ({size_mb:.1f} MB)")


def save_kreise_lookup(lookup, path):
    """Save Kreise lookup dict to a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(lookup, f, ensure_ascii=False, indent=2, sort_keys=True)
    logger.info(f"Saved {len(lookup)} Kreise to {path}")


def load_kreise_lookup(path):
    """Load Kreise lookup dict from JSON file. Returns empty dict if not found."""
    path = Path(path)
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
