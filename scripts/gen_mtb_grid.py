"""Regenerate the TK25 grid-line tables in app/tools/mtb_calc.py.

    uv run --with pyproj python -m scripts.gen_mtb_grid           # print
    uv run --with pyproj python -m scripts.gen_mtb_grid --check   # verify

The sheet grid is defined on the Potsdam datum (see mtb_calc), so producing the
WGS84 tables means transforming those lines once. pyproj is not a dependency of
the app — the tables are the output, and only this script needs it.
"""

import argparse
import sys

from pyproj import Transformer

# EPSG:1777 "DHDN to WGS 84 (2)", a Helmert transform, named rather than left to
# from_crs, which picks the BeTA2007 grid when installed and shifts lines ~2 m.
DHDN_TO_WGS84 = "EPSG:1777"

FIRST_ROW, LAST_ROW = 9, 87
FIRST_COL, LAST_COL = 1, 56

# The datum shift varies along a line by 2-12 m; one value per line is taken at
# mid-country, since reports come from all of Germany.
MID_LON, MID_LAT = 10.4, 51.2


def grid_lines():
    """Return (latitudes south to north, longitudes west to east) in WGS84."""
    transform = Transformer.from_pipeline(DHDN_TO_WGS84).transform
    # EPSG axis order: latitude first.
    lats = [
        transform(56.0 - 0.1 * row, MID_LON)[0]
        for row in range(LAST_ROW + 1, FIRST_ROW - 1, -1)
    ]
    lons = [
        transform(MID_LAT, 17 / 3 + col / 6)[1]
        for col in range(FIRST_COL, LAST_COL + 2)
    ]
    return lats, lons


def as_table(name, values, per_row=8):
    rows = [
        "    " + " ".join(f"{v:.6f}," for v in values[i : i + per_row])
        for i in range(0, len(values), per_row)
    ]
    return f"{name} = (\n" + "\n".join(rows) + "\n)"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare against the committed tables and exit 1 if they differ",
    )
    args = parser.parse_args()

    lats, lons = grid_lines()

    if not args.check:
        print(as_table("LAT_EDGES", lats))
        print(as_table("LON_EDGES", lons))
        return 0

    from app.tools.mtb_calc import LAT_EDGES, LON_EDGES

    drift = [
        (name, index, committed, round(fresh, 6))
        for name, committed_values, fresh_values in (
            ("LAT_EDGES", LAT_EDGES, lats),
            ("LON_EDGES", LON_EDGES, lons),
        )
        for index, (committed, fresh) in enumerate(
            zip(committed_values, fresh_values, strict=True)
        )
        if committed != round(fresh, 6)
    ]
    if drift:
        for name, index, committed, fresh in drift:
            print(f"{name}[{index}]: committed {committed}, regenerated {fresh}")
        print(f"{len(drift)} line(s) differ.", file=sys.stderr)
        return 1

    print(f"{len(lats) + len(lons)} grid lines match the committed tables.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
