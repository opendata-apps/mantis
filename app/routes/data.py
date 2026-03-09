from random import uniform

from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template,
    request,
)
from datetime import date
from sqlalchemy import select, func

from app import db
from app.database.models import (
    TblFundorte,
    TblMeldungen,
    ReportStatus,
)


# Blueprints
data = Blueprint("data", __name__)


def _public_map_filters(min_map_date: date):
    """Return shared visibility rules for public map endpoints."""
    return (
        TblMeldungen.dat_fund_von >= min_map_date,
        TblMeldungen.statuses.contains([ReportStatus.APPR.value]),
    )


@data.route("/auswertungen")
def show_map():
    selected_year = request.args.get("year", None, type=int)
    min_map_date = date(current_app.config["MIN_MAP_YEAR"], 1, 1)

    # Get distinct years from dat_fund_von beginning with MIN_MAP_YEAR
    years_stmt = (
        select(func.extract("year", TblMeldungen.dat_fund_von).label("year"))
        .where(TblMeldungen.dat_fund_von >= min_map_date)
        .distinct()
        .order_by("year")
    )
    years = [int(row[0]) for row in db.session.execute(years_stmt).all()]

    # Validate selected_year exists in available years
    if selected_year is not None and selected_year not in years:
        selected_year = None

    reports_stmt = (
        select(TblMeldungen.id, TblFundorte.latitude, TblFundorte.longitude)
        .join(TblMeldungen.fundort)
        .where(*_public_map_filters(min_map_date))
    )

    if selected_year is not None:
        reports_stmt = reports_stmt.where(
            func.extract("year", TblMeldungen.dat_fund_von) == selected_year
        )

    reports = db.session.execute(reports_stmt).all()

    # Serialize the reports data as a JSON object
    # post_count derived from result set — avoids a separate COUNT query
    koords = []
    for report_id, latitude, longitude in reports:
        try:
            lati = float(latitude)
            long = float(longitude)
        except (ValueError, TypeError):
            continue
        lati, long = obfuscate_location(lati, long)
        koords.append({"report_id": report_id, "latitude": lati, "longitude": long})

    return render_template(
        "map.html",
        reports=koords,
        post_count=len(koords),
        years=years,
        selected_year=selected_year,
    )


@data.route("/get_marker_data/<int:report_id>")
def get_marker_data(report_id):
    "Get the data for a single marker on the map."
    min_map_date = date(current_app.config["MIN_MAP_YEAR"], 1, 1)
    stmt = (
        select(
            TblMeldungen.id,
            TblMeldungen.dat_meld,
            TblMeldungen.dat_fund_von,
            TblFundorte.ort,
            TblFundorte.kreis,
        )
        .join(TblMeldungen.fundort)
        .where(TblMeldungen.id == report_id)
        .where(*_public_map_filters(min_map_date))
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
