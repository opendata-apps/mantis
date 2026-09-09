"""Coordinate rules for Fundorte — accepted range, swap detection, messages.

Everything a coordinate is checked against lives in this module, so the
numbers cannot drift apart between the report form, the reviewer tools and
the CLI.
"""

import re

# Accepted range: Europe per the EPSG:3035 (LAEA Europe) area of use, clipped
# north to 60 and west to -20 — Iceland, Svalbard and the mid-Atlantic are far
# outside the range of Mantis religiosa.
LAT_RANGE = (24.6, 60.0)
LON_RANGE = (-20.0, 44.83)

COORDINATE_RANGES = {"latitude": LAT_RANGE, "longitude": LON_RANGE}
_LABELS = {"latitude": "Breitengrad", "longitude": "Längengrad"}

SWAPPED_MESSAGE = "Breiten- und Längengrad scheinen vertauscht zu sein."

# Optional sign, decimal formats, optional scientific notation. Also rejects
# "nan" and "inf", which would otherwise slip past the range comparison.
_COORDINATE_PATTERN = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")


def _de(bound):
    """Render a bound German-style: 44.83 -> '44,83', 60.0 -> '60'."""
    return f"{bound:g}".replace(".", ",")


# Built from the bounds, so the numbers in the message cannot drift away from
# the numbers that are actually enforced.
RANGE_MESSAGES = {
    kind: f"{_LABELS[kind]} muss zwischen {_de(low)} und {_de(high)} liegen."
    for kind, (low, high) in COORDINATE_RANGES.items()
}

INVALID_MESSAGES = {
    kind: f"{label} ist keine gültige Zahl." for kind, label in _LABELS.items()
}


def parse_coordinate(value):
    """Return the coordinate as a float, or None if it is not a plain number.

    Accepts the comma decimal that mobile keyboards emit, and rejects "nan" and
    "inf" — float() returns those happily and they then slip past every range
    comparison, because a comparison against NaN is always False.
    """
    text = str(value).strip().replace(",", ".")
    if not _COORDINATE_PATTERN.fullmatch(text):
        return None
    return float(text)


def in_range(latitude, longitude):
    """True if both values are inside the accepted range, in the given order."""
    return (
        LAT_RANGE[0] <= latitude <= LAT_RANGE[1]
        and LON_RANGE[0] <= longitude <= LON_RANGE[1]
    )


def validate_coordinate(value, coord_type):
    """Return a parsed coordinate and its validation error, if any."""
    if value is None or not str(value).strip():
        return None, f"{_LABELS[coord_type]} ist erforderlich."

    number = parse_coordinate(value)
    if number is None:
        return None, INVALID_MESSAGES[coord_type]

    low, high = COORDINATE_RANGES[coord_type]
    if not (low <= number <= high):
        return None, RANGE_MESSAGES[coord_type]
    return number, None


def coordinates_look_swapped(latitude, longitude):
    """
    Detect a transposed pair: outside the range as given, inside when swapped.

    Only an unambiguous swap is reported. Where both orders are in range (both
    values inside 24.6..44.83, roughly Greece to the Caucasus) the pair is left
    alone, so a genuine coordinate is never mistaken for a transposed one.

    Examples:
        >>> coordinates_look_swapped(13.4, 52.52)  # Berlin, transposed
        True
        >>> coordinates_look_swapped(52.52, 13.4)  # Berlin
        False
    """
    lat = parse_coordinate(latitude) if latitude is not None else None
    lon = parse_coordinate(longitude) if longitude is not None else None
    if lat is None or lon is None:
        return False

    return not in_range(lat, lon) and in_range(lon, lat)


def validate_coordinate_pair(latitude, longitude):
    """Validate a pair, reporting a transposition before individual range errors."""
    lat, lat_error = validate_coordinate(latitude, "latitude")
    lon, lon_error = validate_coordinate(longitude, "longitude")
    if coordinates_look_swapped(latitude, longitude):
        return lat, lon, [SWAPPED_MESSAGE]
    return lat, lon, [error for error in (lat_error, lon_error) if error]
