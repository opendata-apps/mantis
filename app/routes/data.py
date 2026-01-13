import json
from random import uniform

from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template,
    request,
)
from sqlalchemy import select, func

from app.tools.coordinate_validation import validate_and_normalize_coordinate

from app import db
from app.database.models import (
    TblFundorte,
    TblMeldungen,
    ReportStatus,
)


# Blueprints
data = Blueprint("data", __name__)


@data.route("/auswertungen")
def show_map():
    selected_year = request.args.get("year", None, type=int)

    # Get distinct years from dat_fund_von beginning with MIN_MAP_YEAR
    years_stmt = (
        select(func.extract("year", TblMeldungen.dat_fund_von).label("year"))
        .where(TblMeldungen.dat_fund_von >= f"{current_app.config['MIN_MAP_YEAR']}-01-01")
        .distinct()
        .order_by("year")
    )
    years = [int(row[0]) for row in db.session.execute(years_stmt).all()]

    # Validate selected_year exists in available years
    if selected_year is not None and selected_year not in years:
        selected_year = None

    reports_stmt = (
        select(TblMeldungen.id, TblFundorte.latitude, TblFundorte.longitude)
        .join(TblFundorte, TblMeldungen.fo_zuordnung == TblFundorte.id)
        .where(TblMeldungen.status == ReportStatus.APPR)
    )

    if selected_year is not None:
        reports_stmt = reports_stmt.where(
            func.extract("year", TblMeldungen.dat_fund_von) == selected_year
        )
        # Count should be based on the selected year
        count_stmt = (
            select(func.count())
            .select_from(TblMeldungen)
            .join(TblFundorte, TblMeldungen.fo_zuordnung == TblFundorte.id)
            .where(TblMeldungen.status == ReportStatus.APPR)
            .where(func.extract("year", TblMeldungen.dat_fund_von) == selected_year)
        )
        post_count = db.session.execute(count_stmt).scalar()
    else:
        # Summe aller Meldungen für den Counter
        count_stmt = (
            select(func.count())
            .select_from(TblMeldungen)
            .where(TblMeldungen.dat_fund_von >= f"{current_app.config['MIN_MAP_YEAR']}-01-01")
            .where(TblMeldungen.status == ReportStatus.APPR)
        )
        post_count = db.session.execute(count_stmt).scalar()

    reports = db.session.execute(reports_stmt).all()

    # Serialize the reports data as a JSON object
    koords = []
    for report_id, latitude, longitude in reports:
        # Validate and normalize coordinates using centralized function
        lat_valid, normalized_lat, _ = validate_and_normalize_coordinate(
            latitude, "latitude"
        )
        lon_valid, normalized_lon, _ = validate_and_normalize_coordinate(
            longitude, "longitude"
        )

        if (
            lat_valid
            and lon_valid
            and normalized_lat is not None
            and normalized_lon is not None
        ):
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
    stmt = (
        select(
            TblMeldungen.id,
            TblMeldungen.dat_meld,
            TblMeldungen.dat_fund_von,
            TblFundorte.ort,
            TblFundorte.kreis,
        )
        .join(TblFundorte, TblMeldungen.fo_zuordnung == TblFundorte.id)
        .where(TblMeldungen.id == report_id)
    )
    report = db.session.execute(stmt).first()

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
