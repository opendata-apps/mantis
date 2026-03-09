from app.tools.gemeinde_finder import get_amt_enriched
from app.tools.mtb_calc import get_mtb, point_in_rect


def calculate_spatial_fields(latitude, longitude) -> dict[str, str]:
    """Calculate shared MTB/AGS-derived fields for a coordinate pair."""
    fields = {"mtb": "", "amt": "", "land": "", "kreis": ""}
    if latitude is None or longitude is None:
        return fields

    try:
        lat = float(str(latitude).strip())
        lon = float(str(longitude).strip())
    except (ValueError, TypeError, AttributeError):
        return fields

    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
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
