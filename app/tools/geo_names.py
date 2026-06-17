"""Nearest-neighbour index over GN250 populated places."""

import math
from dataclasses import dataclass
from threading import RLock

from shapely import Point
from shapely.strtree import STRtree


@dataclass(frozen=True, slots=True)
class NearestPlace:
    name: str
    ags: int | None
    kreis: str | None
    distance_m: float


# Lower bound for metres-per-degree across German latitudes (1° lon at ~55°N ≈
# 63.9 km). Dividing a metre radius by this over-estimates the planar dwithin
# pre-filter, so no in-range place is missed; haversine then trims precisely.
_MIN_M_PER_DEG = 60000.0


def _haversine_m(lon1, lat1, lon2, lat2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


class GeoNamesIndex:
    """STRtree over place points; resolves the nearest place to a coordinate."""

    def __init__(self, points, meta):
        self._points = points
        self._meta = meta
        self._tree = STRtree(points) if points else None

    @classmethod
    def from_rows(cls, rows):
        """rows: iterable of (name, ags, kreis, lon, lat)."""
        points, meta = [], []
        for name, ags, kreis, lon, lat in rows:
            points.append(Point(lon, lat))
            meta.append((name, ags, kreis, lon, lat))
        return cls(points, meta)

    def nearest(self, point):
        """point: (lon, lat) -> NearestPlace or None."""
        if not self._tree:
            return None
        lon, lat = point
        i = self._tree.nearest(Point(lon, lat))
        name, ags, kreis, plon, plat = self._meta[i]
        return NearestPlace(
            name=name,
            ags=ags,
            kreis=kreis,
            distance_m=_haversine_m(lon, lat, plon, plat),
        )

    def nearest_places(self, point, radius_m=5000.0, k=12):
        """point: (lon, lat) -> up to k NearestPlace within radius_m, nearest first.

        Unlike nearest(), this returns every place inside the radius — so a closer
        but differently-named point cannot shadow a matching Ortsteil that also lies
        in range. Falls back to the single absolute-nearest place when nothing is
        within radius_m, so callers always have a distance for non-match grading.
        """
        if not self._tree:
            return []
        lon, lat = point
        pt = Point(lon, lat)
        idxs = self._tree.query(
            pt, predicate="dwithin", distance=radius_m / _MIN_M_PER_DEG
        )
        cands = []
        for i in idxs:
            name, ags, kreis, plon, plat = self._meta[i]
            d = _haversine_m(lon, lat, plon, plat)
            if d <= radius_m:
                cands.append(
                    NearestPlace(name=name, ags=ags, kreis=kreis, distance_m=d)
                )
        if not cands:
            i = self._tree.nearest(pt)
            name, ags, kreis, plon, plat = self._meta[i]
            cands.append(
                NearestPlace(
                    name=name,
                    ags=ags,
                    kreis=kreis,
                    distance_m=_haversine_m(lon, lat, plon, plat),
                )
            )
        cands.sort(key=lambda p: p.distance_m)
        return cands[:k]


_index = None
_lock = RLock()


def get_geo_names_index():
    """Process-wide GeoNamesIndex, lazily loaded from the geo_names table."""
    global _index
    with _lock:
        if _index is None:
            from sqlalchemy import select

            from app import db
            from app.database.geo_names import TblGeoNames

            rows = db.session.execute(
                select(
                    TblGeoNames.name,
                    TblGeoNames.ags,
                    TblGeoNames.kreis,
                    TblGeoNames.longitude,
                    TblGeoNames.latitude,
                )
            ).all()
            _index = GeoNamesIndex.from_rows(rows)
        return _index


def reset_geo_names_index():
    """Drop the cached index (after re-seeding or in tests)."""
    global _index
    with _lock:
        _index = None
