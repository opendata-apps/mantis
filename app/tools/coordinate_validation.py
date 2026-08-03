"""Coordinate rules for Fundorte — accepted range, swap detection, messages.

Everything a coordinate is checked against lives in this module, so the
numbers cannot drift apart between the report form, the reviewer tools and
the CLI.
"""

import re
from decimal import Decimal

# Accepted range: the part of Europe Mantis religiosa can plausibly turn up in,
# derived from the EPSG:3035 (LAEA Europe) area of use and trimmed on all four
# sides — Iceland, Svalbard, the mid-Atlantic and the Caucasus are out.
LAT_RANGE = (30.0, 60.0)
LON_RANGE = (-20.0, 30.0)

RANGES = {"latitude": LAT_RANGE, "longitude": LON_RANGE}
_LABELS = {"latitude": "Breitengrad", "longitude": "Längengrad"}

SWAPPED_MESSAGE = "Breiten- und Längengrad scheinen vertauscht zu sein."

# Optional sign, decimal formats, optional scientific notation. Also rejects
# "nan" and "inf", which would otherwise slip past the range comparison.
_COORDINATE_PATTERN = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$")


def _format_bound(value):
    """Render a bound German-style: 60.0 -> '60', 44.83 -> '44,83'."""
    return f"{value:g}".replace(".", ",")


def parse_coordinate(value):
    """Return the coordinate as a float, or None if it is not a plain number.

    Format only — no range check. Read paths that just need to plot what is
    stored should use this instead of the validators below.
    """
    text = str(value).strip().replace(",", ".")  # comma decimals from legacy data
    if not _COORDINATE_PATTERN.fullmatch(text):
        return None
    return float(text)


def normalize(number):
    """Render a parsed coordinate as a plain decimal string.

    str() switches to exponent form below 1e-4 ("1e-05"), which is reachable
    for longitudes near the prime meridian and would be stored that way.
    """
    return format(Decimal(str(number)), "f")


def invalid_number_message(coord_type):
    """The message shown when a coordinate cannot be parsed as a number."""
    return f"{_LABELS[coord_type]} ist keine gültige Zahl."


def range_message(coord_type):
    """The message shown when a coordinate falls outside the accepted range."""
    low, high = RANGES[coord_type]
    label = _LABELS[coord_type]
    return (
        f"{label} muss zwischen {_format_bound(low)} und {_format_bound(high)} liegen."
    )


def in_range(latitude, longitude):
    """True if both values are inside the accepted range, in the given order."""
    return (
        LAT_RANGE[0] <= latitude <= LAT_RANGE[1]
        and LON_RANGE[0] <= longitude <= LON_RANGE[1]
    )


def validate_and_normalize_coordinate(value, coord_type):
    """
    Validate one coordinate and normalize it to a plain decimal string.

    Args:
        value: The coordinate to check (string, float or None)
        coord_type: Either 'latitude' or 'longitude'

    Returns:
        tuple: (normalized_value or None, error_message or None)

    Examples:
        >>> validate_and_normalize_coordinate('52.520000', 'latitude')
        ('52.52', None)

        >>> validate_and_normalize_coordinate('69.2', 'latitude')
        (None, 'Breitengrad muss zwischen 30 und 60 liegen.')
    """
    label = _LABELS[coord_type]

    if value is None or not str(value).strip():
        return None, f"{label} ist erforderlich."

    number = parse_coordinate(value)
    if number is None:
        return None, invalid_number_message(coord_type)

    low, high = RANGES[coord_type]
    if not (low <= number <= high):
        return None, range_message(coord_type)

    return normalize(number), None


def coordinates_look_swapped(latitude, longitude):
    """
    Detect a transposed pair: outside the range as given, inside when swapped.

    Only an unambiguous swap is reported. Where both orders are in range (both
    values inside the overlap of the two ranges) the pair is left alone, so a
    genuine coordinate is never mistaken for a transposed one.

    Examples:
        >>> coordinates_look_swapped(13.4, 52.52)  # Berlin, transposed
        True
        >>> coordinates_look_swapped(52.52, 13.4)  # Berlin
        False
    """
    lat = parse_coordinate(latitude)
    lon = parse_coordinate(longitude)
    if lat is None or lon is None:
        return False

    return not in_range(lat, lon) and in_range(lon, lat)


def validate_coordinate_pair(latitude, longitude):
    """
    Validate both coordinates together.

    A transposed pair is reported as such instead of as two range errors,
    which is the more useful message by far.

    Returns:
        tuple: (normalized_lat or None, normalized_lon or None, errors)
    """
    normalized_lat, lat_error = validate_and_normalize_coordinate(latitude, "latitude")
    normalized_lon, lon_error = validate_and_normalize_coordinate(
        longitude, "longitude"
    )

    if coordinates_look_swapped(latitude, longitude):
        return normalized_lat, normalized_lon, [SWAPPED_MESSAGE]

    return normalized_lat, normalized_lon, [e for e in (lat_error, lon_error) if e]
