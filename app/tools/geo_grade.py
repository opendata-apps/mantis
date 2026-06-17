"""Pure coordinate/address confidence grader (UpHierarchy + distance)."""

from dataclasses import dataclass

from app.tools.normalize_text import names_match_norm, normalize_place_name

# Bumped from 2000: large rural Ortsteile (e.g. Saarmund) sit >2 km from the
# GN250 point centroid yet the pin is still inside the named locality.
_ORTSTEIL_MAX_M = 3000.0

# City-states: the Land *is* the Gemeinde, but BKG splits Berlin into 12 Bezirke,
# so a coordinate there resolves gen='Mitte' etc. — typed ort 'Berlin' can never
# match the Bezirk. Confirm at city-state level using the pin's resolved Land.
_CITY_STATES = {"berlin", "hamburg", "bremen"}

# matched_level -> (grade, base confidence)
_LEVELS = {
    "ORTSTEIL": ("HIGH", 0.95),
    "GEMEINDE": ("HIGH", 0.90),
    "KREIS": ("MEDIUM", 0.60),
    "LAND": ("LOW", 0.35),
    "NONE": ("LOW", 0.15),
    "OUTSIDE_DE": ("LOW", 0.10),
}


@dataclass(frozen=True, slots=True)
class GeoGrade:
    grade: str
    confidence: float
    matched_level: str
    distance_m: float | None
    reasons: list[str]


def _distance_penalty(dist_m):
    if dist_m is None or dist_m <= 500:
        return 0.0
    return min(0.20, (dist_m - 500) / 25000)  # up to -0.20 at ~5 km


def _ags_equal(a, b):
    """Compare AGS values across int / zero-padded-str representations."""
    try:
        return a is not None and b not in (None, "") and int(a) == int(b)
    except (TypeError, ValueError):
        return False


def grade_location(
    lat, lon, stored_land, stored_kreis, stored_ort, *, find_amt, nearest_place
):
    reasons = []
    resolved = find_amt((lon, lat))
    if resolved is None:
        return _make("OUTSIDE_DE", None, ["coordinate resolves outside Germany"])

    land_match = names_match_norm(stored_land or "", resolved["land"] or "")
    kreis_match = names_match_norm(stored_kreis or "", resolved.get("kreis") or "")
    places = nearest_place((lon, lat)) or []
    nearest = places[0] if places else None
    dist = nearest.distance_m if nearest else None

    ort_hit = None
    if stored_ort:
        for cand in places:
            if cand.distance_m > _ORTSTEIL_MAX_M:
                break  # sorted ascending: nothing closer remains
            if names_match_norm(stored_ort, cand.name):
                ort_hit = cand
                break
    if ort_hit is not None:
        reasons.append(
            f"place '{ort_hit.name}' {int(ort_hit.distance_m)} m matches ort"
        )
        return _make("ORTSTEIL", ort_hit.distance_m, reasons)

    resolved_land = resolved["land"] or ""
    if (
        stored_ort
        and normalize_place_name(resolved_land) in _CITY_STATES
        and names_match_norm(stored_ort, resolved_land)
    ):
        reasons.append(f"ort names the city-state '{resolved_land}'")
        return _make("GEMEINDE", dist, reasons)

    gemeinde_match = (
        stored_ort and names_match_norm(stored_ort, resolved["gen"] or "")
    ) or (nearest is not None and _ags_equal(nearest.ags, resolved.get("ags")))
    if gemeinde_match:
        reasons.append(f"ort matches Gemeinde '{resolved['gen']}'")
        return _make("GEMEINDE", dist, reasons)

    if land_match and kreis_match:
        reasons.append("Land and Kreis match; ort does not")
        return _make("KREIS", dist, reasons)
    if land_match:
        reasons.append("only Land matches")
        return _make("LAND", dist, reasons)

    reasons.append(f"no match (resolved {resolved['gen']}, {resolved['land']})")
    return _make("NONE", dist, reasons)


def _make(level, dist, reasons):
    grade, base = _LEVELS[level]
    conf = round(max(0.0, base - _distance_penalty(dist)), 3)
    return GeoGrade(
        grade=grade,
        confidence=conf,
        matched_level=level,
        distance_m=dist,
        reasons=reasons,
    )
