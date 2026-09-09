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


def validate_and_normalize_coordinate(value, coord_type):
    """
    Validate one coordinate and normalize it to a plain decimal string.

    Args:
        value: The coordinate to check (string, float or None)
        coord_type: Either 'latitude' or 'longitude'

    Returns:
        tuple: (is_valid, normalized_value or None, error_message or None)

    Examples:
        >>> validate_and_normalize_coordinate('52.520000', 'latitude')
        (True, '52.52', None)

        >>> validate_and_normalize_coordinate('69.2', 'latitude')
        (False, None, 'Breitengrad muss zwischen 24,6 und 60 liegen.')
    """
    label = _LABELS[coord_type]

    if value is None or not str(value).strip():
        return False, None, f"{label} ist erforderlich."

    number = parse_coordinate(value)
    if number is None:
        return False, None, INVALID_MESSAGES[coord_type]

    low, high = COORDINATE_RANGES[coord_type]
    if not (low <= number <= high):
        return False, None, RANGE_MESSAGES[coord_type]

    return True, str(number), None


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
    """
    Validate both coordinates together.

    A transposed pair is reported as such instead of as two range errors,
    which is the more useful message by far.

    Returns:
        tuple: (is_valid, normalized_lat or None, normalized_lon or None, errors)
    """
    _, normalized_lat, lat_error = validate_and_normalize_coordinate(
        latitude, "latitude"
    )
    _, normalized_lon, lon_error = validate_and_normalize_coordinate(
        longitude, "longitude"
    )

    if coordinates_look_swapped(latitude, longitude):
        return False, normalized_lat, normalized_lon, [SWAPPED_MESSAGE]

    errors = [error for error in (lat_error, lon_error) if error]
    return not errors, normalized_lat, normalized_lon, errors
