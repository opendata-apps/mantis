import json
from random import uniform

from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
)
from app.tools.coordinate_validation import validate_and_normalize_coordinate

from app import db
from app.database.models import (TblFundorte,
                                 TblMeldungen,)
from sqlalchemy import or_

from ..config import Config

# Blueprints
data = Blueprint("data", __name__)

@data.route("/auswertungen")
def show_map():
    selected_year = request.args.get("year", None, type=int)
    
    # Get distinct years from dat_fund_von begginning with MIN_MAP_YEAR
    years = (
        db.session.query(
            db.func.extract("year", TblMeldungen.dat_fund_von).label("year")
        )
        .distinct()
        .order_by("year")
        .filter(TblMeldungen.dat_fund_von >= f"{Config.MIN_MAP_YEAR}-01-01")
    )
    years = [int(year[0]) for year in years]
    
    # Validate selected_year exists in available years
    if selected_year is not None and selected_year not in years:
        selected_year = None

    reports_query = (
        db.session.query(TblMeldungen.id,
                         TblFundorte.latitude,
                         TblFundorte.longitude)
        .join(TblFundorte, TblMeldungen.fo_zuordnung == TblFundorte.id)
        .filter(TblMeldungen.dat_bear.is_not(None))
        .filter(or_(TblMeldungen.deleted.is_(None), TblMeldungen.deleted == False))  # noqa: E712
    )

    if selected_year is not None:
        reports_query = reports_query.filter(
            db.func.extract("year", TblMeldungen.dat_fund_von) == selected_year
        )
        # Count should be based on the selected year
        post_count = reports_query.count()
    else:
        # Summe aller Meldungen für den Counter
        post_count = (
            db.session.query(TblMeldungen)
            .filter(TblMeldungen.dat_fund_von >= f"{Config.MIN_MAP_YEAR}-01-01")
            .filter(TblMeldungen.dat_bear.is_not(None))
            .filter(or_(TblMeldungen.deleted.is_(None), TblMeldungen.deleted == False))  # noqa: E712
            .count()
        )

    reports = reports_query.all()

    # Serialize the reports data as a JSON object
    koords = []
    for report_id, latitude, longitude in reports:
        # Validate and normalize coordinates using centralized function
        lat_valid, normalized_lat, _ = validate_and_normalize_coordinate(latitude, 'latitude')
        lon_valid, normalized_lon, _ = validate_and_normalize_coordinate(longitude, 'longitude')
        
        if lat_valid and lon_valid:
            # Convert back to float for obfuscation
            lati = float(normalized_lat)
            long = float(normalized_lon)
            lati, long = obfuscate_location(lati, long)
            koords.append({"report_id": report_id, "latitude": lati, "longitude": long})

    reportsJson = json.dumps(koords)
    return render_template(
        "map.html",
        reportsJson=reportsJson,
        post_count=post_count,
        years=years,
        selected_year=selected_year,
    )


@data.route("/get_marker_data/<int:report_id>")
def get_marker_data(report_id):
    "Get the data for a single marker on the map."
    report = (
        db.session.query(
            TblMeldungen.id,
            TblMeldungen.dat_meld,
            TblMeldungen.dat_fund_von,
            TblFundorte.ort,
            TblFundorte.kreis,
        )
        .join(TblFundorte, TblMeldungen.fo_zuordnung == TblFundorte.id)
        .filter(TblMeldungen.id == report_id)
        .first()
    )

    if report:
        return jsonify(
            {
                "id": report.id,
                "dat_meld": str(report.dat_meld),
                "dat_fund_von": str(report.dat_fund_von),
                "ort": report.ort,
                "kreis": report.kreis,
            }
        )
    else:
        return jsonify({"error": "Report not found"}), 404


def obfuscate_location(lat, long):
    "Add a small random offset to the given latitude and longitude."
    offset = 0.005  # Adjustable offset
    lat += uniform(-offset, offset)
    long += uniform(-offset, offset)
    return lat, long
