from app.tools.gemeinde_finder import get_amt_enriched
from app.tools.coordinate_validation import validate_coordinate_pair
from app.tools.mtb_calc import get_mtb, point_in_rect


def calculate_spatial_fields(latitude, longitude) -> dict[str, str]:
    """Calculate shared MTB/AGS-derived fields for a coordinate pair."""
    fields = {"mtb": "", "amt": "", "land": "", "kreis": ""}
    if latitude is None or longitude is None:
        return fields

    is_valid, normalized_lat, normalized_lon, _ = validate_coordinate_pair(
        latitude,
        longitude,
    )
    if not is_valid or normalized_lat is None or normalized_lon is None:
        return fields

    lat = float(normalized_lat)
    lon = float(normalized_lon)
    if not point_in_rect((lat, lon)):
        return fields

    fields["mtb"] = get_mtb(lat, lon)
    spatial = get_amt_enriched((lon, lat))
    if spatial:
        fields["amt"] = spatial["amt_string"]
        fields["land"] = spatial["land"]
        fields["kreis"] = spatial["kreis"]

    return fields
