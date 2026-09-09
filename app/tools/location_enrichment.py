from app.tools.gemeinde_finder import get_amt_enriched
from app.tools.coordinate_validation import parse_coordinate
from app.tools.mtb_calc import get_mtb


def calculate_spatial_fields(latitude, longitude) -> dict[str, str]:
    """Calculate shared MTB/AGS-derived fields for a coordinate pair.

    The AGS polygons decide whether the point is in Germany; get_mtb only then
    gets to name the sheet. The TK25 lattice is rectangular and Germany is not,
    so get_mtb still answers 5952 for Praha and 8617 for Zürich — cells that
    were never published as sheets. Without the polygon check first, a foreign
    record would be filed under a German quadrant.
    """
    fields = {"mtb": "", "amt": "", "land": "", "kreis": ""}
    if latitude is None or longitude is None:
        return fields

    lat = parse_coordinate(latitude)
    lon = parse_coordinate(longitude)
    if lat is None or lon is None:
        return fields

    spatial = get_amt_enriched((lon, lat))
    if not spatial:
        return fields

    fields["mtb"] = get_mtb(lat, lon) or ""
    fields["amt"] = spatial["amt_string"]
    fields["land"] = spatial["land"]
    fields["kreis"] = spatial["kreis"]
    return fields


def recalculate_amt_mtb(fundort) -> None:
    """Recalculate AMT, MTB, and fill land/kreis from spatial data."""
    if not fundort:
        return

    spatial_fields = calculate_spatial_fields(fundort.latitude, fundort.longitude)
    fundort.mtb = spatial_fields["mtb"]
    fundort.amt = spatial_fields["amt"]
    # AGS spatial data is authoritative for land/kreis.
    if spatial_fields["land"]:
        fundort.land = spatial_fields["land"]
    if spatial_fields["kreis"]:
        fundort.kreis = spatial_fields["kreis"]
