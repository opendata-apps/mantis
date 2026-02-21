"""
Optimized administrative area (Gemeinde/Amt) finder with caching.

This module provides efficient spatial lookups for determining which administrative
area (Amt) contains a given coordinate point. It uses in-memory caching and spatial
indexing to avoid database queries on every lookup.

Performance: Uses STRtree.query(predicate="within") to push the precise
point-in-polygon check into GEOS C code, eliminating the Python-level loop.
Geometries are simplified (~11m tolerance) to reduce vertex count by ~12%.
A Germany bounding box pre-filter rejects clearly-outside points cheaply.
"""

import json
import os
from collections import namedtuple
from threading import RLock

from shapely import GEOSException, simplify
from shapely.geometry import Point, Polygon, MultiPolygon, shape
from shapely.strtree import STRtree
from sqlalchemy import select
from flask import current_app

from app import db
from app.database.aemter_koordinaten import TblAemterCoordinaten
from app.database.ags import BUNDESLAENDER

# Structured metadata — replaces opaque tuple indexing
AmtRecord = namedtuple("AmtRecord", ["amt_string", "gen", "ags", "land", "kreis"])

# Germany bounding box (generous, includes North Sea islands)
_DE_BOUNDS = (5.8, 15.1, 47.2, 55.2)  # min_lon, max_lon, min_lat, max_lat

# Simplification tolerance in degrees (~11m at 50°N latitude).
# Removes near-duplicate vertices well within GPS/map-click precision.
_SIMPLIFY_TOLERANCE = 0.0001


class GemeindeFinder:
    """Efficient finder for administrative areas using spatial indexing."""

    def __init__(self):
        """Initialize the finder with empty cache."""
        self._geometries = []
        self._metadata = []
        self._tree = None
        self._kreise_lookup = {}
        self._cache_lock = RLock()
        self._is_loaded = False

    def _load_kreise(self):
        """Load Kreise lookup from JSON file."""
        kreise_path = os.path.join(
            os.path.dirname(__file__), "..", "data", "ags_kreise.json"
        )
        try:
            from app.tools.fetch_ags import load_kreise_lookup
            self._kreise_lookup = load_kreise_lookup(kreise_path)
            if self._kreise_lookup:
                current_app.logger.info(
                    f"Loaded {len(self._kreise_lookup)} Kreise for enrichment"
                )
        except Exception as e:
            current_app.logger.warning(f"Could not load Kreise lookup: {e}")
            self._kreise_lookup = {}

    def _load_data(self):
        """Load all administrative area polygons from database."""
        with self._cache_lock:
            if self._is_loaded:
                return

            try:
                current_app.logger.info(
                    "Loading administrative area polygons from database..."
                )
                geometries = []
                metadata = []

                # Load Kreise lookup for enrichment
                self._load_kreise()

                stmt = (
                    select(TblAemterCoordinaten)
                    .order_by(TblAemterCoordinaten.ags)
                )
                rows = db.session.scalars(stmt).all()

                for row in rows:
                    ags = None
                    try:
                        ags = row.ags
                        gen = row.gen
                        properties = row.properties

                        # Parse geometry more safely
                        if isinstance(properties, str):
                            geometry_data = json.loads(properties)
                        else:
                            geometry_data = properties

                        # Create shapely geometry
                        geom = shape(geometry_data)

                        # Format AGS with leading zero if needed
                        ags_str = f"0{ags}" if ags < 10000000 else str(ags)
                        amt_string = f"{ags_str} -- {gen}"

                        # Derive land and kreis from AGS code
                        land_code = ags_str[:2]
                        land_name = BUNDESLAENDER.get(land_code, "")
                        kreis_code = ags_str[:5]
                        kreis_name = self._kreise_lookup.get(kreis_code, "")

                        # Store polygon with its metadata
                        if isinstance(geom, (Polygon, MultiPolygon)):
                            # Simplify to reduce vertex count (~12%) while
                            # preserving topology within ~11m precision.
                            geom = simplify(
                                geom,
                                tolerance=_SIMPLIFY_TOLERANCE,
                                preserve_topology=True,
                            )
                            geometries.append(geom)
                            metadata.append(
                                AmtRecord(amt_string, gen, ags_str, land_name, kreis_name)
                            )
                        else:
                            current_app.logger.warning(
                                f"Skipping non-polygon geometry for {amt_string}"
                            )

                    except (
                        json.JSONDecodeError,
                        KeyError,
                        ValueError,
                        Exception,
                    ) as e:
                        current_app.logger.error(
                            f"Error parsing geometry for row (AGS: {ags}): {e}"
                        )
                        continue

                # Create spatial index for efficient lookups
                if geometries:
                    self._geometries = geometries
                    self._metadata = metadata
                    self._tree = STRtree(geometries)
                    self._is_loaded = True
                    current_app.logger.info(
                        f"Loaded {len(self._geometries)} administrative area polygons"
                    )
                else:
                    current_app.logger.warning("No administrative area polygons loaded")

            except Exception as e:
                current_app.logger.error(
                    f"Failed to load administrative area data: {e}"
                )
                # In production, we should not crash the app if gemeinde data fails to load
                self._geometries = []
                self._metadata = []
                self._tree = None
                self._is_loaded = True  # Mark as loaded to prevent retry loops

    def _query_point(self, point):
        """Internal: find the AmtRecord for a point, or None."""
        if not self._is_loaded:
            self._load_data()

        if not self._tree or not self._geometries:
            return None

        # Fast reject: point outside Germany's bounding box
        lon, lat = point
        min_lon, max_lon, min_lat, max_lat = _DE_BOUNDS
        if not (min_lon <= lon <= max_lon and min_lat <= lat <= max_lat):
            return None

        try:
            point_geom = Point(point)
            # predicate="within" does bbox filtering AND precise point-in-polygon
            # in a single GEOS C call — no Python loop needed.
            indices = self._tree.query(point_geom, predicate="within")
            if len(indices) > 0:
                return self._metadata[indices[0]]
            return None
        except GEOSException as e:
            current_app.logger.error(f"GEOS error finding AMT for point {point}: {e}")
            return None

    def find_amt(self, point):
        """
        Find which administrative area contains the given point.

        Args:
            point: Tuple of (longitude, latitude) coordinates

        Returns:
            String in format "AGS -- Name" if found, None otherwise
        """
        record = self._query_point(point)
        if record is None:
            return None
        return record.amt_string

    def find_amt_enriched(self, point):
        """
        Find administrative area with full hierarchical data.

        Args:
            point: Tuple of (longitude, latitude) coordinates

        Returns:
            Dict with keys {ags, gen, land, kreis, amt_string} if found, None otherwise
        """
        record = self._query_point(point)
        if record is None:
            return None

        kreis_name = record.kreis

        # City-states (Berlin, Hamburg, Bremen): Kreis level equals Land level,
        # which is redundant. Use the Gemeinde name (= Bezirk for Berlin) instead.
        if kreis_name and kreis_name == record.land:
            kreis_name = record.gen

        return {
            "ags": record.ags,
            "gen": record.gen,
            "land": record.land,
            "kreis": kreis_name,
            "amt_string": record.amt_string,
        }

    def reload_cache(self):
        """Force reload of the cache from database."""
        with self._cache_lock:
            self._is_loaded = False
            self._geometries = []
            self._metadata = []
            self._tree = None
            self._kreise_lookup = {}
        self._load_data()

    @property
    def is_loaded(self):
        """Check if data is loaded."""
        return self._is_loaded

    @property
    def polygon_count(self):
        """Get number of loaded polygons."""
        return len(self._geometries)

    @property
    def stats(self):
        """Return polygon count, vertex count, and load status for observability."""
        if not self._geometries:
            return {"loaded": self._is_loaded, "polygons": 0, "vertices": 0}
        total_verts = sum(
            sum(
                len(ring.coords)
                for ring in (
                    [g.exterior] + list(g.interiors)
                    if isinstance(g, Polygon)
                    else [
                        r
                        for p in g.geoms
                        for r in ([p.exterior] + list(p.interiors))
                    ]
                )
            )
            for g in self._geometries
        )
        return {
            "loaded": self._is_loaded,
            "polygons": len(self._geometries),
            "vertices": total_verts,
        }


# Global instance for reuse
_gemeinde_finder = GemeindeFinder()

# Module initialization - logging will happen when used within app context


def get_amt_optimized(point):
    """
    Get AMT string for a point using spatial indexing and caching.

    Args:
        point: Tuple of (longitude, latitude) coordinates

    Returns:
        String in format "AGS -- Name" if found, None otherwise
    """
    return _gemeinde_finder.find_amt(point)


def get_amt_enriched(point):
    """
    Get full administrative hierarchy for a point.

    Returns a dict with ags, gen, land, kreis, amt_string — or None.
    Use this when you need the Bundesland or Kreis name in addition to the AMT string.
    """
    return _gemeinde_finder.find_amt_enriched(point)


def reload_gemeinde_cache():
    """
    Force reload of the administrative area cache.

    Call this if the aemter table has been updated.
    """
    _gemeinde_finder.reload_cache()
