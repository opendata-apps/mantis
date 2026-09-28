"""Administrative area (Gemeinde/Amt) for a coordinate.

The polygons of the aemter table are loaded once per process into a Shapely
STRtree; a lookup is then one GEOS query without touching the database.
"""

import logging
from pathlib import Path

import shapely
from shapely import Point, STRtree
from sqlalchemy import Text, select

from app.extensions import db
from app.database.aemter_koordinaten import TblAemterCoordinaten
from app.database.ags import BUNDESLAENDER
from app.tools.fetch_ags import load_kreise_lookup

logger = logging.getLogger(__name__)

KREISE_PATH = Path(__file__).parent.parent / "data" / "ags_kreise.json"

# The tree, and per tree index the dict get_amt_enriched returns. None until a
# load finds polygons, so a failed or empty load is retried on the next lookup.
_index: tuple[STRtree, list[dict[str, str]]] | None = None


def _area(ags: int, gen: str, kreise: dict[str, str]) -> dict[str, str]:
    ags_str = f"{ags:08d}"
    land = BUNDESLAENDER.get(ags_str[:2], "")
    kreis = kreise.get(ags_str[:5], "")
    # City-states (Berlin, Hamburg, Bremen) are their own Kreis; the Gemeinde
    # (for Berlin, the Bezirk) says more.
    if kreis and kreis == land:
        kreis = gen
    return {
        "ags": ags_str,
        "gen": gen,
        "land": land,
        "kreis": kreis,
        "amt_string": f"{ags_str} -- {gen}",
    }


def _load_index() -> tuple[STRtree, list[dict[str, str]]] | None:
    global _index
    try:
        kreise = load_kreise_lookup(KREISE_PATH)
        # JSONB cast to text and parsed by GEOS skips psycopg's JSON decoding.
        rows = db.session.execute(
            select(
                TblAemterCoordinaten.ags,
                TblAemterCoordinaten.gen,
                TblAemterCoordinaten.properties.cast(Text),
            ).order_by(TblAemterCoordinaten.ags)
        ).all()
    except Exception:
        # Stays unloaded: report.py stores an empty amt for every lookup that
        # finds nothing, so this worker must retry rather than go blind.
        logger.exception("Failed to load administrative area data")
        return None

    geometries = shapely.from_geojson([row[2] for row in rows], on_invalid="ignore")
    polygons, areas = [], []
    for (ags, gen, _), geom in zip(rows, geometries, strict=True):
        if geom is None or geom.geom_type not in ("Polygon", "MultiPolygon"):
            logger.warning("Skipping AGS %s: not a polygon", ags)
            continue
        polygons.append(geom)
        areas.append(_area(ags, gen, kreise))

    if not polygons:
        logger.warning("No administrative area polygons loaded")
        return None
    _index = (STRtree(polygons), areas)
    logger.info("Loaded %d administrative area polygons", len(polygons))
    return _index


def get_amt_enriched(point) -> dict[str, str] | None:
    """Return ags, gen, land, kreis and amt_string for a (lon, lat) point, or None."""
    index = _index or _load_index()
    if index is None:
        return None
    tree, areas = index
    hits = tree.query(Point(point), predicate="within")
    return dict(areas[hits[0]]) if len(hits) else None


def reload_gemeinde_cache() -> None:
    """Rebuild the polygon cache after the aemter table changed."""
    global _index
    _index = None
    _load_index()


def warm_gemeinde_cache() -> bool:
    """Build the polygon cache now; False if no polygons could be loaded."""
    return (_index or _load_index()) is not None
