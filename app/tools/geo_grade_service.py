"""Glue between stored fields and the pure grader; returns column values."""

from datetime import datetime, timezone

from app.tools.gemeinde_finder import get_amt_enriched
from app.tools.geo_grade import grade_location
from app.tools.geo_names import get_geo_names_index


def grade_fundort_fields(lat, lon, stored_land, stored_kreis, stored_ort):
    """Return a dict of geo_* column values for one location."""
    index = get_geo_names_index()
    grade = grade_location(
        lat,
        lon,
        stored_land,
        stored_kreis,
        stored_ort,
        find_amt=get_amt_enriched,
        nearest_place=index.nearest if index else (lambda pt: None),
    )
    return {
        "geo_grade": grade.grade,
        "geo_confidence": grade.confidence,
        "geo_matched_level": grade.matched_level,
        "geo_reasons": grade.reasons,
        "geo_graded_at": datetime.now(timezone.utc),
    }
