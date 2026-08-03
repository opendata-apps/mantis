from app.tools.gemeinde_finder import get_amt_enriched
from app.tools.coordinate_validation import in_range, parse_coordinate
from app.tools.mtb_calc import get_mtb, point_in_rect


def calculate_spatial_fields(latitude, longitude) -> dict[str, str]:
    """Calculate shared MTB/AGS-derived fields for a coordinate pair."""
    fields = {"mtb": "", "amt": "", "land": "", "kreis": ""}

    lat = parse_coordinate(latitude)
    lon = parse_coordinate(longitude)
    if lat is None or lon is None or not in_range(lat, lon):
        return fields

    if not point_in_rect((lat, lon)):
        return fields

    fields["mtb"] = get_mtb(lat, lon)
    spatial = get_amt_enriched((lon, lat))
    if spatial:
        fields["amt"] = spatial["amt_string"]
        fields["land"] = spatial["land"]
        fields["kreis"] = spatial["kreis"]

    return fields
