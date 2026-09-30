import hmac
from datetime import date

from flask import (
    Blueprint,
    abort,
    current_app,
    jsonify,
    render_template,
    request,
)
from sqlalchemy import Select, func, select

from app.database.models import (
    TblFundorte,
    TblMeldungen,
)
from app.extensions import db
from app.tools.coordinate_validation import LAT_RANGE, LON_RANGE

# Blueprints
data = Blueprint("data", __name__)


def _public_map_filters(min_map_date: date):
    """Return shared visibility rules for public map endpoints."""
    return (
        TblMeldungen.dat_fund_von >= min_map_date,
        TblMeldungen.is_approved,
    )


def _map_years(min_map_date: date) -> list[int]:
    """Years with reports since MIN_MAP_YEAR, oldest first."""
    stmt = (
        select(func.extract("year", TblMeldungen.dat_fund_von).label("year"))
        .where(TblMeldungen.dat_fund_von >= min_map_date)
        .distinct()
        .order_by("year")
    )
    return [int(row[0]) for row in db.session.execute(stmt).all()]


def _map_request() -> tuple[list[int], int | None, Select]:
    """Years, the valid selected year or None, and the map's points query."""
    min_map_date = date(current_app.config["MIN_MAP_YEAR"], 1, 1)
    years = _map_years(min_map_date)
    selected_year = request.args.get("year", None, type=int)
    if selected_year not in years:
        selected_year = None

    stmt = (
        select(TblMeldungen.id, TblFundorte.latitude, TblFundorte.longitude)
        .join(TblMeldungen.fundort)
        .where(
            *_public_map_filters(min_map_date),
            TblFundorte.latitude.between(*LAT_RANGE),
            TblFundorte.longitude.between(*LON_RANGE),
        )
    )
    if selected_year is not None:
        stmt = stmt.where(
            func.extract("year", TblMeldungen.dat_fund_von) == selected_year
        )
    return years, selected_year, stmt


@data.route("/auswertungen")
def show_map():
    years, selected_year, points_stmt = _map_request()
    post_count = db.session.scalar(
        select(func.count()).select_from(points_stmt.subquery())
    )
    return render_template(
        "map.html",
        post_count=post_count,
        years=years,
        selected_year=selected_year,
    )


@data.route("/auswertungen/punkte")
def map_points():
    """The map's markers as `[id, lat, lon]`, fetched by map-page.js."""
    _, _, points_stmt = _map_request()
    points = []
    for report_id, latitude, longitude in db.session.execute(points_stmt):
        lat, lon = obfuscate_location(latitude, longitude, report_id)
        # 4 decimals is ~11 m, far below the offset; it halves the gzip size.
        points.append([report_id, round(lat, 4), round(lon, 4)])

    response = jsonify(points)
    response.cache_control.public = True
    response.cache_control.max_age = 300
    return response


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

    if report is None:
        abort(404)
    return render_template("partials/_marker_popup.html", report=report)


def obfuscate_location(lat, long, report_id):
    """Offset a point so the map cannot resolve it to somebody's garden.

    The offset must not vary between requests: repeated draws for one report
    average out to the true coordinate, and the endpoint serves `ort` and the
    sighting date beside it. Measured, 500 views of a per-request offset leave
    9 m of error.

    SECRET_KEY keys the hash because this repository is public — the report id
    alone would let anyone re-run this function and subtract it.
    """
    offset = 0.005
    secret = current_app.config["SECRET_KEY"].encode()
    digest = hmac.digest(secret, str(report_id).encode(), "sha256")
    # Two 32-bit words, each mapped onto [-offset, offset].
    dlat, dlon = (int.from_bytes(digest[i : i + 4]) / 2**31 - 1 for i in (0, 4))
    return lat + dlat * offset, long + dlon * offset
