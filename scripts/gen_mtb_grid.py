"""Regenerate the TK25 grid-line tables in app/tools/mtb_calc.py.

    uv run --with pyproj python scripts/gen_mtb_grid.py           # print
    uv run --with pyproj python scripts/gen_mtb_grid.py --check   # verify

The sheet grid is defined on the Potsdam datum (see mtb_calc), so producing the
WGS84 tables means transforming those lines once. pyproj is not a dependency of
the app — the tables are the output, and only this script needs it.

The Helmert parameters are pinned rather than left to
``Transformer.from_crs("EPSG:4314", "EPSG:4326")``, because that picks whatever
operation is available on the machine: with the de_adv_BETA2007 NTv2 grid
installed it silently uses that instead, and the tables shift by up to 2 m. The
pinned pipeline is EPSG's "DHDN to WGS 84 (2)", which is what produced the
committed tables.

BeTA2007, the AdV's federally mandated NTv2 grid (Beschluss 118/9, 2006), is
the more accurate transformation, and it fits this job unusually well: its own
grid is laid out on the TK25 lattice — 10' x 6' from 5°30'/47°00' — so every
line here lands exactly on one of its nodes with nothing interpolated.

It is still not used, because it is not what limits the result. Measured
against the official Brandenburg Blattschnitt (LGB, 299 sheets), swapping the
transform moves the row lines by 0.08 m; moving MID_LAT/MID_LON from
mid-country to Brandenburg moves them by 2.2 m. The evaluation point below
dominates the transform by an order of magnitude, so paying for a grid file
fetched over the network at generation time would buy nothing measurable.
"""

import argparse
import sys

from pyproj import Transformer

# EPSG "DHDN to WGS 84 (2)", 7-parameter Helmert, stated accuracy 3 m.
DHDN_TO_WGS84 = (
    "+proj=pipeline +step +proj=unitconvert +xy_in=deg +xy_out=rad "
    "+step +proj=push +v_3 +step +proj=cart +ellps=bessel "
    "+step +proj=helmert +x=598.1 +y=73.7 +z=418.2 "
    "+rx=0.202 +ry=0.045 +rz=-2.455 +s=6.7 +convention=position_vector "
    "+step +inv +proj=cart +ellps=WGS84 +step +proj=pop +v_3 "
    "+step +proj=unitconvert +xy_in=rad +xy_out=deg"
)

FIRST_ROW, LAST_ROW = 9, 87
FIRST_COL, LAST_COL = 1, 56

# One number has to stand for a whole grid line, but the datum shift varies
# along it, so the line moves 2-12 m depending on where it is evaluated. This
# point is the largest lever in the whole module, and it is deliberately set
# mid-country rather than over Brandenburg, where most reports come from:
#
#   against the 299 official LGB sheets     rows     cols
#     evaluated here (10.4/51.2)            2.45 m   2.31 m
#     evaluated at 13.4/52.4 (Brandenburg)  0.27 m   0.50 m
#
# Brandenburg is nine times better there and correspondingly worse everywhere
# else, and the app takes reports from all of Germany. The national compromise
# already puts only ~0.04% of coordinates on the wrong sheet — in Brandenburg
# 8 of 20000, none further than 3.5 m from a sheet boundary — so there is
# nothing here worth trading away the rest of the country for.
MID_LON, MID_LAT = 10.4, 51.2


def grid_lines():
    """Return (latitudes south to north, longitudes west to east) in WGS84."""
    transform = Transformer.from_pipeline(DHDN_TO_WGS84).transform
    lats = [
        transform(MID_LON, 56.0 - 0.1 * row)[1]
        for row in range(LAST_ROW + 1, FIRST_ROW - 1, -1)
    ]
    lons = [
        transform(17 / 3 + col / 6, MID_LAT)[0]
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
