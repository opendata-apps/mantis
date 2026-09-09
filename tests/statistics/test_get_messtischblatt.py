"""TK25 sheet numbers.

Every expected value here was read off the published Blattschnitt (orchids.de
TK25-Raster, 2023-02), not off our own output. The sheet the app picks is the
sheet the reporter would find on the printed map, or the number is wrong.
"""

import pytest
from app.tools.mtb_calc import get_mtb


@pytest.mark.parametrize(
    "lat,lon,expected_mtb",
    [
        (51.738052, 13.440228, "4246"),  # Trebbin
        (52.520008, 13.404954, "3446"),  # Berlin Mitte -> 3446 Berlin (Nord)
        # Potsdam's centre lies just south of the 52.398586 row line, so it
        # belongs to 3644 Potsdam (Süd), not to the sheet that carries the name
        # 3544 Potsdam (Nord).
        (52.390569, 13.064473, "3644"),
        (51.339695, 12.373075, "4640"),  # Leipzig
        (51.050407, 13.737262, "4948"),  # Dresden
        (55.018900, 8.435600, "0916"),  # List auf Sylt, northernmost row
    ],
)
def test_get_mtb_for_various_locations(lat, lon, expected_mtb):
    assert get_mtb(lat, lon) == expected_mtb


@pytest.mark.parametrize(
    "lat,lon",
    [
        (48.208176, 16.373819),  # Wien, east of the last column
        (52.229676, 21.012229),  # Warszawa
        (41.902782, 12.496366),  # Roma, south of the first row
        (55.700000, 9.000000),  # Jylland, north of the last row
    ],
)
def test_get_mtb_returns_none_outside_the_sheet_index(lat, lon):
    """Outside the index there is no sheet, and saying so beats inventing one."""
    assert get_mtb(lat, lon) is None


def test_get_mtb_still_answers_inside_the_lattice_beyond_the_border():
    """The lattice is rectangular, so Praha and Zürich land on unpublished cells.

    Callers must confirm the point is in Germany themselves — see
    calculate_spatial_fields, which asks the AGS polygons first.
    """
    assert get_mtb(50.075538, 14.437800) == "5952"  # Praha
    assert get_mtb(47.376888, 8.541694) == "8617"  # Zürich


# The line between rows 48 and 49 runs at 51.098733 N, the one between rows 47
# and 48 at 51.198722 N, and the line between columns 43 and 44 at 12.998350 E.
@pytest.mark.parametrize(
    "lat,lon,expected_mtb",
    [
        (51.099233, 13.0, "4844"),  # 55 m north of the 48/49 line -> row 48
        (51.098233, 13.0, "4944"),  # 55 m south of it -> row 49
        (51.199222, 13.0, "4744"),  # 55 m north of the 47/48 line -> row 47
        (52.0, 12.998850, "3944"),  # 39 m east of the 43/44 line -> column 44
        (52.0, 12.997850, "3943"),  # 39 m west of it -> column 43
    ],
)
def test_get_mtb_boundary_precision(lat, lon, expected_mtb):
    """A point a few dozen metres from a grid line lands on the right side."""
    assert get_mtb(lat, lon) == expected_mtb


def test_grid_line_belongs_to_the_sheet_north_and_east_of_it():
    """Documents the tie-break, so a later refactor cannot flip it silently."""
    assert get_mtb(51.098733, 13.0) == "4844"
    assert get_mtb(52.0, 12.998350) == "3944"


def _boundaries(fixed, low, high, vary_latitude):
    """Latitudes (or longitudes) where the sheet number changes.

    Found by asking get_mtb, so this stays true whether the sheet is looked up
    in a table, computed, or fetched from a service.
    """

    def sheet(value):
        return get_mtb(value, fixed) if vary_latitude else get_mtb(fixed, value)

    step, found, previous, at = 0.005, [], sheet(low), low
    while at < high:
        at, current = at + step, sheet(at + step)
        if current == previous:
            continue
        lo, hi = at - step, at
        for _ in range(40):  # bisect down to well under a millimetre
            mid = (lo + hi) / 2
            if sheet(mid) == previous:
                lo = mid
            else:
                hi = mid
        found.append((lo + hi) / 2)
        previous = current
    return found


@pytest.mark.parametrize(
    "fixed,low,high,vary_latitude,expected_count,spacing",
    [
        (13.0, 47.25, 55.05, True, 78, 0.1),
        (52.0, 5.9, 15.1, False, 55, 1 / 6),
    ],
)
def test_sheets_tile_the_grid_evenly(
    fixed, low, high, vary_latitude, expected_count, spacing
):
    """Walking across the country must cross one sheet edge every 6' / 10'.

    A mistyped digit in the grid would move an edge and show up here as an
    uneven step. The exhaustive check is ``python -m scripts.gen_mtb_grid
    --check``; this one only needs the public function.
    """
    edges = _boundaries(fixed, low, high, vary_latitude)
    assert len(edges) == expected_count
    steps = [b - a for a, b in zip(edges, edges[1:], strict=False)]
    assert max(abs(step - spacing) for step in steps) < 0.0002
