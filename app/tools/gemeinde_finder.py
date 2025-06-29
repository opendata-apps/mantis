"""
Optimized administrative area (Gemeinde/Amt) finder with caching.

This module provides efficient spatial lookups for determining which administrative
area (Amt) contains a given coordinate point. It uses in-memory caching and spatial
indexing to avoid database queries on every lookup.
"""
import json
from functools import lru_cache
from threading import RLock
from shapely.geometry import shape, Point, Polygon, MultiPolygon
from shapely.strtree import STRtree
from sqlalchemy import text
from flask import current_app
from app import db


class GemeindeFinder:
    """Efficient finder for administrative areas using spatial indexing."""
    
    def __init__(self):
        """Initialize the finder with empty cache."""
        self._polygons = []
        self._spatial_index = None
        self._cache_lock = RLock()
        self._is_loaded = False
    
    def _load_data(self):
        """Load all administrative area polygons from database."""
        with self._cache_lock:
            if self._is_loaded:
                return
            
            try:
                current_app.logger.info("Loading administrative area polygons from database...")
                polygons = []
                
                with db.engine.connect() as conn:
                    # Use more efficient query that only selects needed columns
                    result = conn.execute(
                        text("SELECT ags, gen, properties FROM aemter ORDER BY ags")
                    )
                    
                    for row in result:
                        ags = None
                        try:
                            ags, gen, properties = row
                            
                            # Parse geometry more safely
                            if isinstance(properties, str):
                                # Handle the string replacement issue properly
                                geometry_data = json.loads(properties)
                            else:
                                geometry_data = properties
                            
                            # Create shapely geometry
                            geom = shape(geometry_data)
                            
                            # Format AGS with leading zero if needed
                            ags_str = f"0{ags}" if ags < 10000000 else str(ags)
                            amt_string = f"{ags_str} -- {gen}"
                            
                            # Store polygon with its metadata
                            if isinstance(geom, (Polygon, MultiPolygon)):
                                polygons.append((geom, amt_string, gen))
                            else:
                                current_app.logger.warning(f"Skipping non-polygon geometry for {amt_string}")
                                
                        except (json.JSONDecodeError, KeyError, ValueError, Exception) as e:
                            current_app.logger.error(f"Error parsing geometry for row (AGS: {ags}): {e}")
                            continue
                
                # Create spatial index for efficient lookups
                if polygons:
                    self._polygons = polygons
                    # STRtree expects just the geometries
                    geometries = [p[0] for p in polygons]
                    self._spatial_index = STRtree(geometries)
                    self._is_loaded = True
                    current_app.logger.info(f"Loaded {len(self._polygons)} administrative area polygons")
                else:
                    current_app.logger.warning("No administrative area polygons loaded")
                    
            except Exception as e:
                current_app.logger.error(f"Failed to load administrative area data: {e}")
                # In production, we should not crash the app if gemeinde data fails to load
                self._polygons = []
                self._spatial_index = None
                self._is_loaded = True  # Mark as loaded to prevent retry loops
    
    def find_amt(self, point):
        """
        Find which administrative area contains the given point.
        
        Args:
            point: Tuple of (longitude, latitude) coordinates
            
        Returns:
            String in format "AGS -- Name" if found, None otherwise
        """
        # Ensure data is loaded
        if not self._is_loaded:
            self._load_data()
        
        if not self._spatial_index or not self._polygons:
            return None
        
        try:
            # Create point geometry
            point_geom = Point(point)
            
            # Use spatial index to find potential matches
            # This is much faster than checking every polygon
            potential_indices = self._spatial_index.query(point_geom, predicate='intersects')
            
            # Check actual containment for potential matches
            for idx in potential_indices:
                if idx < len(self._polygons):
                    polygon, amt_string, gen = self._polygons[idx]
                    if polygon.contains(point_geom):
                        return amt_string
            
            return None
            
        except Exception as e:
            current_app.logger.error(f"Error finding AMT for point {point}: {e}")
            return None
    
    def find_amt_with_details(self, point):
        """
        Find administrative area with additional details.
        
        Args:
            point: Tuple of (longitude, latitude) coordinates
            
        Returns:
            Dictionary with 'amt', 'ags', and 'name' if found, None otherwise
        """
        amt_string = self.find_amt(point)
        if amt_string:
            # Parse the format "AGS -- Name"
            parts = amt_string.split(" -- ", 1)
            if len(parts) == 2:
                return {
                    'amt': amt_string,
                    'ags': parts[0],
                    'name': parts[1]
                }
        return None
    
    def reload_cache(self):
        """Force reload of the cache from database."""
        with self._cache_lock:
            self._is_loaded = False
            self._polygons = []
            self._spatial_index = None
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
    Optimized version of get_amt_full_scan using spatial indexing and caching.
    
    This is a drop-in replacement for the original function but much more efficient.
    
    Args:
        point: Tuple of (longitude, latitude) coordinates
        
    Returns:
        String in format "AGS -- Name" if found, None otherwise
    """
    return _gemeinde_finder.find_amt(point)


def reload_gemeinde_cache():
    """
    Force reload of the administrative area cache.
    
    Call this if the aemter table has been updated.
    """
    _gemeinde_finder.reload_cache()


def get_gemeinde_cache_status():
    """
    Get the current status of the gemeinde cache.
    
    Returns:
        Dictionary with cache status information
    """
    return {
        'is_loaded': _gemeinde_finder.is_loaded,
        'polygon_count': _gemeinde_finder.polygon_count,
        'cache_type': 'in-memory',
        'implementation': 'optimized_strtree'
    }


# For backward compatibility, keep the original function name
# but use the optimized implementation
def get_amt_full_scan(point):
    """
    Legacy function name for compatibility.
    Now uses optimized implementation with caching.
    """
    try:
        return get_amt_optimized(point)
    except Exception as e:
        current_app.logger.error(f"Error in get_amt_full_scan for point {point}: {e}")
        return None  # Return None instead of crashing in production
