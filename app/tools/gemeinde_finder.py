"""
Optimized administrative area (Gemeinde/Amt) finder with caching.

This module provides efficient spatial lookups for determining which administrative
area (Amt) contains a given coordinate point. It uses in-memory caching and spatial
indexing to avoid database queries on every lookup.
"""

import json
import os
from threading import RLock
from shapely.geometry import shape, Point, Polygon, MultiPolygon
from shapely.strtree import STRtree
from sqlalchemy import select
from flask import current_app
from app import db
from app.database.aemter_koordinaten import TblAemterCoordinaten
from app.database.ags import BUNDESLAENDER


class GemeindeFinder:
    """Efficient finder for administrative areas using spatial indexing."""

    def __init__(self):
        """Initialize the finder with empty cache."""
        self._polygons = []
        self._spatial_index = None
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
                polygons = []

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
                            polygons.append(
                                (geom, amt_string, gen, ags_str, land_name, kreis_name)
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
                if polygons:
                    self._polygons = polygons
                    # STRtree expects just the geometries
                    geometries = [p[0] for p in polygons]
                    self._spatial_index = STRtree(geometries)
                    self._is_loaded = True
                    current_app.logger.info(
                        f"Loaded {len(self._polygons)} administrative area polygons"
                    )
                else:
                    current_app.logger.warning("No administrative area polygons loaded")

            except Exception as e:
                current_app.logger.error(
                    f"Failed to load administrative area data: {e}"
                )
                # In production, we should not crash the app if gemeinde data fails to load
                self._polygons = []
                self._spatial_index = None
                self._is_loaded = True  # Mark as loaded to prevent retry loops

    def _query_point(self, point):
        """Internal: find the polygon tuple for a point, or None."""
        if not self._is_loaded:
            self._load_data()

        if not self._spatial_index or not self._polygons:
            return None

        try:
            point_geom = Point(point)
            potential_indices = self._spatial_index.query(
                point_geom, predicate="intersects"
            )
            for idx in potential_indices:
                if idx < len(self._polygons):
                    entry = self._polygons[idx]
                    polygon = entry[0]
                    if polygon.contains(point_geom):
                        return entry
            return None
        except Exception as e:
            current_app.logger.error(f"Error finding AMT for point {point}: {e}")
            return None

    def find_amt(self, point):
        """
        Find which administrative area contains the given point.

        Args:
            point: Tuple of (longitude, latitude) coordinates

        Returns:
            String in format "AGS -- Name" if found, None otherwise
        """
        entry = self._query_point(point)
        if entry is None:
            return None
        return entry[1]  # amt_string

    def find_amt_enriched(self, point):
        """
        Find administrative area with full hierarchical data.

        Args:
            point: Tuple of (longitude, latitude) coordinates

        Returns:
            Dict with keys {ags, gen, land, kreis, amt_string} if found, None otherwise
        """
        entry = self._query_point(point)
        if entry is None:
            return None
        _, amt_string, gen, ags_str, land_name, kreis_name = entry

        # City-states (Berlin, Hamburg, Bremen): Kreis level equals Land level,
        # which is redundant. Use the Gemeinde name (= Bezirk for Berlin) instead.
        if kreis_name and kreis_name == land_name:
            kreis_name = gen

        return {
            "ags": ags_str,
            "gen": gen,
            "land": land_name,
            "kreis": kreis_name,
            "amt_string": amt_string,
        }

    def reload_cache(self):
        """Force reload of the cache from database."""
        with self._cache_lock:
            self._is_loaded = False
            self._polygons = []
            self._spatial_index = None
            self._kreise_lookup = {}
        self._load_data()

    @property
    def is_loaded(self):
        """Check if data is loaded."""
        return self._is_loaded

    @property
    def polygon_count(self):
        """Get number of loaded polygons."""
        return len(self._polygons)


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
