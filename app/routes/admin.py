from datetime import datetime, timedelta
from io import BytesIO
import tempfile
import xlsxwriter
from app import db
import app.database.alldata as ad
import app.database.full_text_search as fts
from app.database.models import (
    TblFundortBeschreibung,
    TblFundorte,
    TblMeldungen,
    TblMeldungUser,
    TblUsers,
    TblAllData,
    ReportStatus,
)
from app.database.user_feedback import TblUserFeedback
from app.database.feedback_type import TblFeedbackType
from flask import session
from flask import (
    Blueprint,
    abort,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    url_for,
)
from sqlalchemy import inspect, or_, cast, String, update, select, func
from sqlalchemy.exc import SQLAlchemyError
from flask_sqlalchemy.pagination import Pagination
from app.tools.check_reviewer import reviewer_required
import shutil
from werkzeug.utils import secure_filename
from pathlib import Path
from flask import current_app
from app.tools.send_reviewer_email import send_email
from app.tools.mtb_calc import get_mtb, pointInRect
from app.tools.gemeinde_finder import get_amt_full_scan
from app.tools.coordinate_validation import validate_and_normalize_coordinate
from typing import Optional, Any


class CompoundSelectPagination(Pagination):
    """Pagination for compound select statements (multiple ORM entities).

    Flask-SQLAlchemy's db.paginate() uses scalars() internally, which only returns
    the first entity in compound selects. This subclass properly handles Row objects
    containing multiple entities by using execute() without scalars().

    Per Flask-SQLAlchemy docs: "compound selects will not return the expected results"
    with db.paginate(). This class follows the Pagination template method pattern.

    Usage:
        stmt = select(Entity1, Entity2).join(...)
        pagination = CompoundSelectPagination(
            select=stmt,
            session=db.session,
            page=1,
            per_page=20,
        )
        for row in pagination.items:
            entity1, entity2 = row  # Access entities from Row object
    """

    def _query_items(self) -> list:
        """Execute the select statement without scalars() to preserve all entities."""
        stmt = self._query_args["select"]
        stmt = stmt.limit(self.per_page).offset(self._query_offset)
        session = self._query_args["session"]
        # Use execute() instead of scalars() to get full Row objects
        return list(session.execute(stmt).unique().all())

    def _query_count(self) -> int:
        """Count total rows for pagination."""
        stmt = self._query_args["select"]
        sub = stmt.order_by(None).subquery()
        session = self._query_args["session"]
        return session.execute(select(func.count()).select_from(sub)).scalar()

import os

# Blueprints
admin = Blueprint("admin", __name__)

# Add this constant at the top of the file
NON_EDITABLE_FIELDS = {
    "meldungen": ["id", "fo_zuordnung"],
    "beschreibung": ["id"],
    "fundorte": ["id", "ablage", "beschreibung"],
    "melduser": ["id", "id_finder", "id_meldung", "id_user"],
    "users": ["id", "user_id"],
    "all_data_view": [
        "meldungen_id",
        "fo_zuordnung",
        "fundorte_id",
        "beschreibung_id",
        "id_user",
        "user_id",
    ],
}


def recalculate_amt_mtb(fundort):
    """Recalculate AMT and MTB values for a fundort based on its coordinates."""
    if not fundort or not fundort.latitude or not fundort.longitude:
        return

    try:
        # Strip whitespace and convert to float
        lat = float(fundort.latitude.strip())
        lon = float(fundort.longitude.strip())

        if -90 <= lat <= 90 and -180 <= lon <= 180:
            if pointInRect((lat, lon)):
                fundort.mtb = get_mtb(lat, lon)
                fundort.amt = get_amt_full_scan((lon, lat))
            else:
                # Coordinates outside Brandenburg region
                fundort.mtb = ""
                fundort.amt = ""
        else:
            # Invalid coordinate range
            fundort.mtb = ""
            fundort.amt = ""
    except (ValueError, TypeError, AttributeError):
        # If coordinates can't be parsed, clear AMT/MTB
        fundort.mtb = ""
        fundort.amt = ""


@admin.route("/reviewer/<usrid>")
def reviewer(usrid):
    "This function is used to display the reviewer page"
    # Fetch the user based on the 'usrid' parameter
    user = db.session.scalar(select(TblUsers).where(TblUsers.user_id == usrid))

    # If the user doesn't exist or the role isn't 9, return 404
    if not user or user.user_rolle != "9":
        abort(403)

    now = datetime.now()
    # Get the user_name of the logged in user_id
    user_name = user.user_name
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 21, type=int)
    last_updated = session.get("last_updated")
    # Store the userid in session
    session["user_id"] = usrid

    # Handle case where session datetime might have timezone info from serialization
    if last_updated and hasattr(last_updated, "tzinfo") and last_updated.tzinfo:
        last_updated = last_updated.replace(tzinfo=None)
    if last_updated is None or now - last_updated > timedelta(minutes=1):
        fts.refresh_materialized_view(db)
        session["last_updated"] = now

    filter_status = request.args.get("statusInput", "offen")
    filter_type = request.args.get("typeInput", None)
    sort_order = request.args.get("sort_order", "id_desc")  # Changed default to desc
    search_query = request.args.get("q", None)
    search_type = request.args.get("search_type", "full_text")
    date_from = request.args.get("dateFrom", None)
    date_to = request.args.get("dateTo", None)

    image_path = current_app.config["UPLOAD_FOLDER"]
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    if "statusInput" not in request.args and "sort_order" not in request.args:
        return redirect(
            url_for(
                "admin.reviewer",
                usrid=usrid,
                statusInput="offen",
                sort_order="id_desc",  # Changed to desc
            )
        )

    # Get filtered select statement using our reusable function
    stmt = get_filtered_query(
        filter_status=filter_status,
        filter_type=filter_type,
        search_query=search_query,
        search_type=search_type,
        date_from=date_from,
        date_to=date_to,
    )

    # Apply sort order
    if sort_order == "id_asc":
        stmt = stmt.order_by(TblMeldungen.id.asc())
    elif sort_order == "id_desc":
        stmt = stmt.order_by(TblMeldungen.id.desc())

    # Use CompoundSelectPagination for multi-entity selects
    # Flask-SQLAlchemy's db.paginate() uses scalars() which only returns the first entity
    # Per docs: "compound selects will not return the expected results" with db.paginate()
    paginated_sightings = CompoundSelectPagination(
        select=stmt,
        session=db.session,
        page=page,
        per_page=per_page,
        max_per_page=100,
        error_out=False,
    )

    # Process the joined data for the template
    reported_sightings = []

    # Fetch all approvers in a single query to avoid N+1 problem
    bearb_ids = [
        row[0].bearb_id for row in paginated_sightings.items if row[0].bearb_id
    ]
    approvers = {}
    if bearb_ids:
        approvers = {
            u.user_id: u.user_name
            for u in db.session.scalars(
                select(TblUsers).where(TblUsers.user_id.in_(bearb_ids))
            ).all()
        }

    for row in paginated_sightings.items:
        meldung, fundort, beschreibung, _, user = row
        sighting = meldung
        sighting.fundort = fundort
        sighting.beschreibung = beschreibung
        sighting.ort = fundort.ort
        sighting.plz = fundort.plz
        sighting.kreis = fundort.kreis
        sighting.land = fundort.land
        if sighting.bearb_id:
            sighting.approver_username = approvers.get(sighting.bearb_id, "Unknown")
        reported_sightings.append(sighting)

    return render_template(
        "admin/admin.html",
        user_id=usrid,
        paginated_sightings=paginated_sightings,
        reported_sightings=reported_sightings,
        tables=tables,
        image_path=image_path,
        user_name=user_name,
        filters={"status": filter_status, "type": filter_type},
        current_filter_status=filter_status,
        current_sort_order=sort_order,
        search_query=search_query,
        search_type=search_type,
    )


@admin.route("/change_mantis_meta_data/<int:id>", methods=["POST"])
@reviewer_required
def change_mantis_meta_data(id):
    "Change mantis report metadata"
    new_data = request.form.get("new_data")
    fieldname = request.form.get("type")

    if not new_data or not fieldname:
        return jsonify({"error": "Missing data in request"}), 400

    sighting_meldung = db.session.get(TblMeldungen, id)
    if not sighting_meldung:
        return jsonify({"error": "Report not found"}), 404

    if fieldname in ["fo_quelle", "anm_bearbeiter"]:
        sighting_obj = sighting_meldung
    else:
        fo_id = sighting_meldung.fo_zuordnung
        sighting_obj = db.session.get(TblFundorte, fo_id)
        if not sighting_obj:
            return jsonify({"error": "Fundort not found"}), 404

    sighting_meldung.bearb_id = session["user_id"]
    update_fields = {
        "fo_quelle": "fo_quelle",
        "anm_bearbeiter": "anm_bearbeiter",
        "amt": "amt",
        "mtb": "mtb",
        "latitude": "latitude",
        "longitude": "longitude",
        "plz": "plz",
        "ort": "ort",
        "strasse": "strasse",
        "kreis": "kreis",
        "land": "land",
    }

    field_to_update = update_fields.get(fieldname)
    if field_to_update:
        # Normalize coordinate values before storing
        if fieldname in ["latitude", "longitude"]:
            is_valid, normalized_value, error_msg = validate_and_normalize_coordinate(
                new_data, fieldname
            )
            if not is_valid:
                return jsonify({"error": error_msg}), 400
            new_data = normalized_value

        setattr(sighting_obj, field_to_update, new_data)

        # If coordinates were updated, recalculate AMT and MTB
        if fieldname in ["latitude", "longitude"]:
            recalculate_amt_mtb(sighting_obj)

        try:
            db.session.commit()
            current_app.logger.info(
                f"Report {id} metadata updated: {fieldname} to {new_data} by user {session['user_id']}"
            )

            return jsonify({"success": True})
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error updating report {id}: {e}")
            return jsonify({"error": "Database error"}), 500
    else:
        return jsonify({"error": "Invalid field type"}), 400


@admin.route("/update_coordinates/<int:id>", methods=["POST"])
@reviewer_required
def update_coordinates(id):
    """Update both coordinates at once and recalculate AMT/MTB"""
    try:
        data = request.get_json()
        if not data or "latitude" not in data or "longitude" not in data:
            return jsonify({"error": "Missing coordinates"}), 400

        # Validate and normalize both coordinates
        lat_valid, normalized_lat, lat_error = validate_and_normalize_coordinate(
            data["latitude"], "latitude"
        )
        lon_valid, normalized_lon, lon_error = validate_and_normalize_coordinate(
            data["longitude"], "longitude"
        )

        if not lat_valid:
            return jsonify({"error": lat_error}), 400
        if not lon_valid:
            return jsonify({"error": lon_error}), 400

        # Get the sighting and its location
        sighting = db.session.get(TblMeldungen, id)
        if not sighting:
            return jsonify({"error": "Report not found"}), 404

        fundort = db.session.get(TblFundorte, sighting.fo_zuordnung)
        if not fundort:
            return jsonify({"error": "Location not found"}), 404

        # Update coordinates and recalculate
        fundort.latitude = normalized_lat
        fundort.longitude = normalized_lon
        recalculate_amt_mtb(fundort)

        # Update bearer ID
        sighting.bearb_id = session["user_id"]

        db.session.commit()

        return jsonify(
            {"success": True, "amt": fundort.amt or "", "mtb": fundort.mtb or ""}
        )

    except ValueError:
        return jsonify({"error": "Invalid coordinate format"}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating coordinates for report {id}: {e}")
        return jsonify({"error": str(e)}), 500


@admin.route("/admin/images/<path:filename>")
@reviewer_required
def report_img(filename):
    """Serve report images securely from the upload folder."""
    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"], filename, mimetype="image/webp"
    )


@admin.route("/toggle_approve_sighting/<int:id>", methods=["POST"])
@reviewer_required
def toggle_approve_sighting(id):
    "Find ID and mark as approved with a date in column dat_bear"

    # Find the report by id
    sighting = db.session.get(TblMeldungen, id)
    if sighting:
        # Toggle between APPR and OPEN status
        if sighting.status != ReportStatus.APPR:
            sighting.status = ReportStatus.APPR
            sighting.dat_bear = datetime.now()
        else:
            # Revert to OPEN status
            sighting.status = ReportStatus.OPEN
            sighting.dat_bear = None
        sighting.bearb_id = session["user_id"]
        db.session.commit()
        current_app.logger.debug(
            f"Sighting {id} status toggled to {sighting.status}. dat_bear set to {sighting.dat_bear}"
        )
    else:
        current_app.logger.error(f"Sighting {id} not found for approval toggle.")
        return jsonify({"error": "Report not found"}), 404

    if current_app.config.get("REVIEWERMAIL", False):
        stmt = (
            select(
                TblMeldungen,
                TblFundorte,
                TblFundortBeschreibung,
                TblMeldungUser,
                TblUsers,
            )
            .join(TblFundorte, TblMeldungen.fo_zuordnung == TblFundorte.id)
            .join(
                TblFundortBeschreibung,
                TblFundorte.beschreibung == TblFundortBeschreibung.id,
            )
            .join(TblMeldungUser, TblMeldungen.id == TblMeldungUser.id_meldung)
            .join(TblUsers, TblMeldungUser.id_user == TblUsers.id)
            .where(TblMeldungen.id == id)
        )
        sighting = db.session.execute(stmt).first()

        if sighting:
            dbdata = {}
            for part in sighting:
                part_dict = {
                    c.name: getattr(part, c.name) for c in part.__table__.columns
                }
                dbdata.update(part_dict)

            if dbdata["user_kontakt"]:
                try:
                    send_email(dbdata)
                except Exception as e:
                    current_app.logger.error(
                        f"Email not sent for sighting {id}. Error: {e}"
                    )
            else:
                current_app.logger.error(
                    f"Email not sent for sighting {id}. No email address found."
                )
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Sighting not found for email sending."}), 404
    else:
        return jsonify({"success": True})


@admin.route("/get_sighting/<int:id>", methods=["GET", "POST"])
@reviewer_required
def get_sighting(id):
    "Find the sighting by id and return it as a JSON object"
    # Find the report by id
    stmt = (
        select(TblMeldungen, TblFundorte, TblFundortBeschreibung, TblMeldungUser, TblUsers)
        .join(TblFundorte, TblMeldungen.fo_zuordnung == TblFundorte.id)
        .join(
            TblFundortBeschreibung,
            TblFundorte.beschreibung == TblFundortBeschreibung.id,
        )
        .join(TblMeldungUser, TblMeldungen.id == TblMeldungUser.id_meldung)
        .join(TblUsers, TblMeldungUser.id_user == TblUsers.id)
        .where(TblMeldungen.id == id)
    )
    sighting = db.session.execute(stmt).first()

    if sighting:
        # Convert sighting to a dictionary and return it
        sighting_dict = {}
        for part in sighting:
            part_dict = {c.name: getattr(part, c.name) for c in part.__table__.columns}
            sighting_dict.update(part_dict)

        # Get feedback information for this user
        meldung, fundort, beschreibung, melduser, user = sighting
        feedback_stmt = (
            select(TblUserFeedback, TblFeedbackType)
            .join(
                TblFeedbackType, TblUserFeedback.feedback_type_id == TblFeedbackType.id
            )
            .where(TblUserFeedback.user_id == user.id)
        )
        feedback = db.session.execute(feedback_stmt).first()

        if feedback:
            user_feedback, feedback_type = feedback
            sighting_dict["feedback_type"] = feedback_type.name
            sighting_dict["feedback_detail"] = user_feedback.source_detail
        else:
            sighting_dict["feedback_type"] = None
            sighting_dict["feedback_detail"] = None

        return jsonify(sighting_dict)
    else:
        return jsonify({"error": "Report not found"}), 404


@admin.route("/delete_sighting/<int:id>", methods=["POST"])
@reviewer_required
def delete_sighting(id):
    "Soft-delete sighting based on id"
    # Find the report by id
    sighting = db.session.get(TblMeldungen, id)
    if not sighting:
        return jsonify({"error": "Report not found"}), 404

    # Set status to DEL and keep deleted=True for backward compatibility
    sighting.status = ReportStatus.DEL
    sighting.deleted = True
    sighting.bearb_id = session["user_id"]
    db.session.commit()
    return jsonify({"success": True})


@admin.route("/undelete_sighting/<int:id>", methods=["POST"])
@reviewer_required
def undelete_sighting(id):
    "Undelete sighting based on id"
    # Find the report by id
    sighting = db.session.get(TblMeldungen, id)
    if not sighting:
        return jsonify({"error": "Report not found"}), 404

    # Set status to OPEN and clear deleted flag
    sighting.status = ReportStatus.OPEN
    sighting.deleted = False
    sighting.bearb_id = session["user_id"]
    db.session.commit()
    return jsonify({"success": True})


@admin.route("/set_status/<int:id>", methods=["POST"])
@reviewer_required
def set_status(id):
    """Set report status to a specific value."""
    status_str = request.form.get("status")

    # Validate and convert string to enum
    try:
        new_status = ReportStatus(status_str)
    except ValueError:
        valid_statuses = ReportStatus.values()
        return jsonify({"error": f"Invalid status. Must be one of: {valid_statuses}"}), 400

    sighting = db.session.get(TblMeldungen, id)
    if not sighting:
        return jsonify({"error": "Report not found"}), 404

    old_status = sighting.status
    sighting.status = new_status
    sighting.bearb_id = session["user_id"]

    # Handle deleted flag for backward compatibility
    sighting.deleted = (new_status == ReportStatus.DEL)

    # Handle dat_bear for approval tracking
    if new_status == ReportStatus.APPR and not sighting.dat_bear:
        sighting.dat_bear = datetime.now()
    elif new_status != ReportStatus.APPR:
        sighting.dat_bear = None

    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to update status for sighting {id}: {e}")
        return jsonify({"error": "Failed to update status"}), 500

    current_app.logger.debug(
        f"Sighting {id} status changed from {old_status} to {new_status}"
    )
    return jsonify({
        "success": True,
        "message": f"Status changed to {ReportStatus.get_display_name(new_status.value)}",
        "status": new_status.value,
        "status_display": ReportStatus.get_display_name(new_status.value),
    }), 200


@admin.route("/change_mantis_gender/<int:id>", methods=["POST"])
@reviewer_required
def change_gender(id):
    "Change mantis gender or type"
    new_gender = request.form.get("new_gender")

    sighting = db.session.get(TblMeldungen, id)
    if sighting is None:
        abort(404, description="Sighting not found")

    # Reset all gender columns to 0
    sighting.art_m = 0
    sighting.art_w = 0
    sighting.art_n = 0
    sighting.art_o = 0
    sighting.art_f = 0

    # Update the specified gender to 1
    if new_gender == "M":
        sighting.art_m = 1
    elif new_gender == "W":
        sighting.art_w = 1
    elif new_gender == "N":
        sighting.art_n = 1
    elif new_gender == "O":
        sighting.art_o = 1
    elif new_gender == "F":
        sighting.art_f = 1

    sighting.bearb_id = session["user_id"]
    db.session.commit()

    return jsonify({"success": True})


@admin.route("/change_mantis_count/<int:id>", methods=["POST"])
@reviewer_required
def change_mantis_count(id):
    "Change mantis count for a specific type"
    new_count = request.form.get("new_count")
    mantis_type = request.form.get("type")
    sighting = db.session.get(TblMeldungen, id)
    if sighting is None:
        abort(404, description="Sighting not found")

    # Update the count for the specified mantis type
    if mantis_type == "Männchen":
        sighting.art_m = new_count
    elif mantis_type == "Weibchen":
        sighting.art_w = new_count
    elif mantis_type == "Nymphe":
        sighting.art_n = new_count
    elif mantis_type == "Oothek":
        sighting.art_o = new_count
    elif mantis_type == "Andere":
        sighting.art_f = new_count
    elif mantis_type == "Anzahl":
        sighting.tiere = new_count

    sighting.bearb_id = session["user_id"]
    db.session.commit()

    return jsonify({"success": True})


@admin.route("/admin/export/xlsx/<string:value>")
@reviewer_required
def export_data(value):
    """Export data from the database as an Excel file.

    Memory-optimized for large exports using:
    - yield_per() for streaming DB results in batches
    - xlsxwriter constant_memory mode for row-by-row writing
    - Temp file on disk instead of BytesIO for large exports
    """
    try:
        current_time = datetime.now().strftime("%d.%m.%Y_%H%M")

        # Get parameters from request, using same defaults as reviewer function
        filter_status = request.args.get("statusInput", "offen")
        filter_type = request.args.get("typeInput", "all")
        search_query = request.args.get("q", None)
        search_type = request.args.get("search_type", "full_text")
        date_from = request.args.get("dateFrom", None)
        date_to = request.args.get("dateTo", None)

        # Get filtered select statement based on export type
        if value == "all":
            filename = f"Alle_Meldungen_{current_time}.xlsx"
            stmt = get_filtered_query(filter_status="all")
        elif value == "accepted":
            filename = f"Akzeptierte_Meldungen_{current_time}.xlsx"
            stmt = get_filtered_query(filter_status="bearbeitet")
        elif value == "non_accepted":
            filename = f"Nicht_akzeptierte_Meldungen_{current_time}.xlsx"
            stmt = get_filtered_query(filter_status="offen")
        elif value == "searched":
            filename = f"Suchergebnisse_{current_time}.xlsx"
            stmt = get_filtered_query(
                filter_status=filter_status,
                filter_type=filter_type,
                search_query=search_query,
                search_type=search_type,
                date_from=date_from,
                date_to=date_to,
            )
        else:
            abort(404, description="Resource not found")

        # First pass: Get count and collect approver IDs for pre-fetching
        # This is a lightweight query that doesn't load full ORM objects
        count_result = db.session.execute(
            select(func.count()).select_from(stmt.subquery())
        ).scalar()
        row_count = count_result or 0

        # Threshold for using memory-optimized mode (constant_memory)
        # Below this, use standard mode with table formatting
        LARGE_EXPORT_THRESHOLD = 5000

        # Pre-fetch all approvers in a single query to avoid N+1 problem
        # Use a subquery aliased properly to avoid cartesian product warning
        subq = stmt.subquery()
        bearb_id_stmt = select(subq.c.bearb_id).where(subq.c.bearb_id.isnot(None))
        bearb_ids = [bid for (bid,) in db.session.execute(bearb_id_stmt).all()]
        approvers = {}
        if bearb_ids:
            approvers = {
                u.user_id: u.user_name
                for u in db.session.scalars(
                    select(TblUsers).where(TblUsers.user_id.in_(set(bearb_ids)))
                ).all()
            }

        # Column definitions with fixed widths (avoids needing full data scan)
        columns = [
            ("ID", 8),
            ("Status", 12),
            ("Fund-Datum", 12),
            ("Melde-Datum", 12),
            ("Bearbeitungs-Datum", 18),
            ("Anzahl Tiere", 12),
            ("Männchen", 10),
            ("Weibchen", 10),
            ("Nymphen", 10),
            ("Ootheken", 10),
            ("Andere", 10),
            ("Fundort-Quelle", 14),
            ("Anmerkung Melder", 30),
            ("Anmerkung Bearbeiter", 30),
            ("PLZ", 8),
            ("Ort", 20),
            ("Straße", 25),
            ("Kreis", 20),
            ("Land", 15),
            ("Amt", 25),
            ("MTB", 8),
            ("Längengrad", 12),
            ("Breitengrad", 12),
            ("Beschreibung", 30),
            ("Melder Name", 20),
            ("Melder Kontakt", 25),
            ("Bearbeiter", 20),
        ]

        # Use temp file for large exports, BytesIO for small ones
        use_large_mode = row_count > LARGE_EXPORT_THRESHOLD
        if use_large_mode:
            # Large export: use temp file + constant_memory mode
            temp_file = tempfile.NamedTemporaryFile(
                suffix=".xlsx", delete=False, dir=current_app.config.get("TEMP_DIR")
            )
            output_path = temp_file.name
            temp_file.close()
            workbook = xlsxwriter.Workbook(
                output_path, {"constant_memory": True, "tmpdir": "/tmp"}
            )
        else:
            # Small export: use BytesIO (faster for small files)
            output = BytesIO()
            workbook = xlsxwriter.Workbook(output, {"in_memory": True})

        worksheet = workbook.add_worksheet("Daten")

        # Create formats
        header_format = workbook.add_format(
            {"bold": True, "bg_color": "#4472C4", "font_color": "white", "border": 1}
        )
        date_format = workbook.add_format({"num_format": "dd.mm.yyyy"})

        # Write headers and set column widths
        for col_idx, (col_name, col_width) in enumerate(columns):
            worksheet.write(0, col_idx, col_name, header_format)
            worksheet.set_column(col_idx, col_idx, col_width)

        # Stream data using yield_per for memory efficiency
        # This fetches rows in batches instead of loading all into memory
        streaming_stmt = stmt.execution_options(yield_per=1000)
        result = db.session.execute(streaming_stmt)

        row_idx = 1
        for row in result:
            meldung, fundort, beschreibung, melduser, user = row

            # Write row data directly (no intermediate dict/list)
            worksheet.write(row_idx, 0, meldung.id)
            worksheet.write(row_idx, 1, ReportStatus.get_display_name(meldung.status))
            worksheet.write(
                row_idx,
                2,
                meldung.dat_fund_von.strftime("%d.%m.%Y")
                if meldung.dat_fund_von
                else "",
            )
            worksheet.write(
                row_idx,
                3,
                meldung.dat_meld.strftime("%d.%m.%Y") if meldung.dat_meld else "",
            )
            worksheet.write(
                row_idx,
                4,
                meldung.dat_bear.strftime("%d.%m.%Y") if meldung.dat_bear else "",
            )
            worksheet.write(row_idx, 5, meldung.tiere)
            worksheet.write(row_idx, 6, meldung.art_m)
            worksheet.write(row_idx, 7, meldung.art_w)
            worksheet.write(row_idx, 8, meldung.art_n)
            worksheet.write(row_idx, 9, meldung.art_o)
            worksheet.write(row_idx, 10, meldung.art_f)
            worksheet.write(row_idx, 11, meldung.fo_quelle)
            worksheet.write(row_idx, 12, meldung.anm_melder)
            worksheet.write(row_idx, 13, meldung.anm_bearbeiter)
            worksheet.write(row_idx, 14, fundort.plz)
            worksheet.write(row_idx, 15, fundort.ort)
            worksheet.write(row_idx, 16, fundort.strasse)
            worksheet.write(row_idx, 17, fundort.kreis)
            worksheet.write(row_idx, 18, fundort.land)
            worksheet.write(row_idx, 19, fundort.amt)
            worksheet.write(row_idx, 20, fundort.mtb)
            worksheet.write(row_idx, 21, fundort.longitude)
            worksheet.write(row_idx, 22, fundort.latitude)
            worksheet.write(row_idx, 23, beschreibung.beschreibung)
            worksheet.write(row_idx, 24, user.user_name)
            worksheet.write(row_idx, 25, user.user_kontakt)
            # Approver (pre-fetched to avoid N+1)
            worksheet.write(
                row_idx,
                26,
                approvers.get(meldung.bearb_id, "") if meldung.bearb_id else "",
            )

            row_idx += 1

        # Add table formatting only for small exports (constant_memory can't use tables)
        if not use_large_mode and row_idx > 1:
            column_settings = [{"header": col[0]} for col in columns]
            worksheet.add_table(
                0,
                0,
                row_idx - 1,
                len(columns) - 1,
                {"columns": column_settings, "style": "Table Style Medium 9"},
            )

        # Freeze header row
        worksheet.freeze_panes(1, 0)

        workbook.close()

        # Send the file
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if use_large_mode:
            # Send temp file and clean up after
            response = send_file(
                output_path, mimetype=mime, as_attachment=True, download_name=filename
            )

            # Schedule cleanup of temp file after response is sent
            @response.call_on_close
            def cleanup():
                try:
                    Path(output_path).unlink(missing_ok=True)
                except Exception:
                    pass

            return response
        else:
            output.seek(0)
            return send_file(
                output, mimetype=mime, as_attachment=True, download_name=filename
            )
    except Exception:
        current_app.logger.exception("Error in export_data")
        return jsonify({"error": "An error occurred during export"}), 500


def update_report_image_date(report_id, new_date):
    """Update the image location when dat_fund_von changes"""
    # Handle both string and datetime objects
    if isinstance(new_date, str):
        new_date_obj = datetime.strptime(new_date, "%Y-%m-%d")
    else:
        new_date_obj = new_date

    # Fetch the report
    report = db.session.scalar(select(TblMeldungen).where(TblMeldungen.id == report_id))
    if not report:
        return {"error": "Report not found"}, 404

    # Fetch the corresponding fundorte record
    fundorte_record = db.session.scalar(
        select(TblFundorte).where(TblFundorte.id == report.fo_zuordnung)
    )
    if not fundorte_record or not fundorte_record.ablage:
        # No image to move
        return {"status": "no_image"}, 200

    base_dir = Path(current_app.config["UPLOAD_FOLDER"])
    old_image_path = base_dir / fundorte_record.ablage

    # Check if the old image file exists
    if not old_image_path.exists():
        return {"error": f"Image file not found: {fundorte_record.ablage}"}, 404

    old_dir, old_filename = os.path.split(old_image_path)
    # Extract location and user id from filename
    filename_parts = old_filename.rsplit("-", 2)
    if len(filename_parts) != 3:
        return {"error": f"Invalid filename format: {old_filename}"}, 400

    location = filename_parts[0]
    usrid_with_ext = filename_parts[2]
    usrid = usrid_with_ext.replace(".webp", "")

    new_dir_path = _create_directory(new_date_obj)
    new_filename = _create_filename(location, usrid, new_date_obj)
    new_file_path = new_dir_path / (new_filename + ".webp")

    # Skip if source and destination are the same
    if str(old_image_path) == str(new_file_path):
        return {"status": "no_change"}, 200

    try:
        # Move the file
        shutil.move(str(old_image_path), str(new_file_path))

        # Check if old directory is empty, if yes, delete it
        if os.path.exists(old_dir) and not os.listdir(old_dir):
            os.rmdir(old_dir)
            # Also check parent year directory
            old_year_dir = os.path.dirname(old_dir)
            if os.path.exists(old_year_dir) and not os.listdir(old_year_dir):
                os.rmdir(old_year_dir)

    except IOError as e:
        return {"error": f"Failed to move file: {e}"}, 500

    # Update the path in fundorte table
    fundorte_record.ablage = str(new_file_path.relative_to(base_dir))
    db.session.commit()

    return {
        "status": "success",
        "old_path": str(old_image_path),
        "new_path": str(new_file_path),
    }, 200


def _create_directory(new_date):
    "Create a directory for the new image if it doesn't exist yet"
    year = new_date.strftime("%Y")
    base_dir = Path(current_app.config["UPLOAD_FOLDER"])
    dir_path = base_dir / year / new_date.strftime("%Y-%m-%d")
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def _create_filename(location, usrid, new_date):
    "Create a filename for the new image and location"
    new_timestamp = new_date.strftime("%Y%m%d%H%M%S")
    # Generate the filename without the .webp extension
    return "{}-{}-{}".format(
        secure_filename(location), new_timestamp, secure_filename(usrid)
    )


def get_filtered_query(
    filter_status: Optional[str] = None,
    filter_type: Optional[str] = None,
    search_query: Optional[str] = None,
    search_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
):
    """Get filtered select statement based on parameters.

    Returns a SQLAlchemy 2.0 style select statement that can be used with
    db.paginate() or db.session.execute().
    """
    # Always include all necessary joins for better performance
    stmt = (
        select(TblMeldungen, TblFundorte, TblFundortBeschreibung, TblMeldungUser, TblUsers)
        .join(TblFundorte, TblMeldungen.fo_zuordnung == TblFundorte.id)
        .join(
            TblFundortBeschreibung,
            TblFundorte.beschreibung == TblFundortBeschreibung.id,
        )
        .join(TblMeldungUser, TblMeldungen.id == TblMeldungUser.id_meldung)
        .join(TblUsers, TblMeldungUser.id_user == TblUsers.id)
    )

    # Apply filter conditions based on 'filter_status' using new status column
    if filter_status == "bearbeitet":
        stmt = stmt.where(TblMeldungen.status == ReportStatus.APPR)
    elif filter_status == "offen":
        stmt = stmt.where(TblMeldungen.status == ReportStatus.OPEN)
    elif filter_status == "geloescht":
        stmt = stmt.where(TblMeldungen.status == ReportStatus.DEL)
    elif filter_status == "informiert":
        stmt = stmt.where(TblMeldungen.status == ReportStatus.INFO)
    elif filter_status == "unklar":
        stmt = stmt.where(TblMeldungen.status == ReportStatus.UNKL)
    elif filter_status == "all":
        # No filter - show all statuses
        pass
    elif search_query:
        # If there's a search query, don't apply any status filter
        pass
    else:
        # Default behavior: Exclude deleted items
        stmt = stmt.where(TblMeldungen.status != ReportStatus.DEL)

    # Apply type filter
    if filter_type:
        if filter_type == "maennlich":
            stmt = stmt.where(TblMeldungen.art_m >= 1)
        elif filter_type == "weiblich":
            stmt = stmt.where(TblMeldungen.art_w >= 1)
        elif filter_type == "oothek":
            stmt = stmt.where(TblMeldungen.art_o >= 1)
        elif filter_type == "Nymphe":
            stmt = stmt.where(TblMeldungen.art_n >= 1)
        elif filter_type == "andere":
            stmt = stmt.where(TblMeldungen.art_f >= 1)
        elif filter_type == "nicht_bestimmt":
            stmt = stmt.where(
                TblMeldungen.art_m.is_(None),
                TblMeldungen.art_w.is_(None),
                TblMeldungen.art_o.is_(None),
                TblMeldungen.art_n.is_(None),
                TblMeldungen.art_f.is_(None),
            )

    # Apply search
    if search_query:
        try:
            if search_type == "id":
                try:
                    search_id = int(search_query)
                    stmt = stmt.where(TblMeldungen.id == search_id)
                except ValueError:
                    search_type = "full_text"

            if search_type == "full_text":
                if "@" in search_query:
                    stmt = stmt.where(
                        TblUsers.user_kontakt.ilike(f"%{search_query}%")
                    )
                else:
                    # Use the new FTS search method
                    matching_ids = fts.FullTextSearch.search(search_query)
                    if matching_ids:
                        stmt = stmt.where(TblMeldungen.id.in_(matching_ids))
                    else:
                        # If no FTS matches, return empty result
                        stmt = stmt.where(TblMeldungen.id == -1)
        except Exception as e:
            current_app.logger.error(f"Search error: {e}")
            stmt = stmt.where(
                TblMeldungen.id == -1
            )  # Return empty result set on error

    # Apply date filters
    if date_from and date_to:
        try:
            date_from_obj = datetime.strptime(date_from, "%d.%m.%Y")
            date_to_obj = datetime.strptime(date_to, "%d.%m.%Y")
            stmt = stmt.where(
                TblMeldungen.dat_fund_von.between(date_from_obj, date_to_obj)
            )
        except ValueError as e:
            current_app.logger.error(f"Date parsing error: {e}")
            stmt = stmt.where(TblMeldungen.id == -1)
    elif date_from:
        try:
            date_from_obj = datetime.strptime(date_from, "%d.%m.%Y")
            stmt = stmt.where(TblMeldungen.dat_fund_von >= date_from_obj)
        except ValueError as e:
            current_app.logger.error(f"Date parsing error: {e}")
            stmt = stmt.where(TblMeldungen.id == -1)
    elif date_to:
        try:
            date_to_obj = datetime.strptime(date_to, "%d.%m.%Y")
            stmt = stmt.where(TblMeldungen.dat_fund_von <= date_to_obj)
        except ValueError as e:
            current_app.logger.error(f"Date parsing error: {e}")
            stmt = stmt.where(TblMeldungen.id == -1)

    return stmt


@admin.route("/alldata")
@reviewer_required
def database_view():
    last_updated = session.get("last_updated_all_data_view")
    now = datetime.now()
    # Handle case where session datetime might have timezone info from serialization
    if last_updated and hasattr(last_updated, "tzinfo") and last_updated.tzinfo:
        last_updated = last_updated.replace(tzinfo=None)
    if last_updated is None or now - last_updated > timedelta(minutes=1):
        # if last_updated is None or now - last_updated > timedelta(minutes=1):
        ad.refresh_materialized_view(db)
        session["last_updated_all_data_view"] = now
    # Get user_id from session, default to None if not found
    user_id = session.get("user_id")

    return render_template("admin/database.html", user_id=user_id)


@admin.route("/admin/get_table_data/<table_name>")
@reviewer_required
def get_table_data(table_name):
    if table_name != "all_data_view":
        return jsonify({"error": "Only all_data_view is available"}), 403
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        search = request.args.get("search", "")
        search_type = request.args.get("search_type", "full_text")
        sort_column = request.args.get("sort_column", "meldungen_id")
        sort_direction = request.args.get("sort_direction", "asc")

        # Check if it's time to refresh the materialized view
        last_updated = session.get("last_updated_all_data_view")
        now = datetime.now()
        # Handle case where session datetime might have timezone info from serialization
        if last_updated and hasattr(last_updated, "tzinfo") and last_updated.tzinfo:
            last_updated = last_updated.replace(tzinfo=None)
        if last_updated is None or (now - last_updated > timedelta(minutes=1)):
            ad.refresh_materialized_view(db)
            session["last_updated_all_data_view"] = now

        # Get the table object - we only work with TblAllData now
        table = TblAllData.__table__

        columns = [column.name for column in table.columns]

        # Validate sort_column to prevent SQL injection
        if sort_column not in columns:
            sort_column = "meldungen_id"

        # Create a select statement
        stmt = select(table)

        # Apply search filter if search term is provided
        if search:
            if search_type == "id":
                try:
                    # Try to convert search term to integer for ID search
                    search_id = int(search)
                    stmt = stmt.where(table.c.meldungen_id == search_id)
                except ValueError:
                    # If conversion fails, return no results
                    stmt = stmt.where(
                        table.c.meldungen_id == -1
                    )  # This ensures no results
            else:  # full_text search
                search_filters = []
                for column in table.columns:
                    if isinstance(column.type, db.String):
                        search_filters.append(column.ilike(f"%{search}%"))
                    elif isinstance(column.type, (db.Integer, db.Float)):
                        search_filters.append(cast(column, String).ilike(f"%{search}%"))
                if search_filters:
                    stmt = stmt.where(or_(*search_filters))

        # Apply sorting
        if sort_direction == "asc":
            stmt = stmt.order_by(table.c[sort_column].asc())
        else:
            stmt = stmt.order_by(table.c[sort_column].desc())

        # Get total count for pagination
        total_items_stmt = select(func.count()).select_from(table)
        if search:
            if search_type == "id":
                try:
                    search_id = int(search)
                    total_items_stmt = total_items_stmt.where(
                        table.c.meldungen_id == search_id
                    )
                except ValueError:
                    total_items_stmt = total_items_stmt.where(
                        table.c.meldungen_id == -1
                    )
            else:
                if search_filters:
                    total_items_stmt = total_items_stmt.where(or_(*search_filters))
        total_items = db.session.execute(total_items_stmt).scalar()

        # Apply pagination
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)

        # Execute query and get results
        results = db.session.execute(stmt).fetchall()

        def get_standard_type(column_type):
            if isinstance(column_type, db.Integer):
                return "integer"
            elif isinstance(column_type, db.String):
                return "string"
            elif isinstance(column_type, db.Boolean):
                return "boolean"
            elif isinstance(column_type, db.Date):
                return "date"
            elif isinstance(column_type, db.DateTime):
                return "datetime"
            elif isinstance(column_type, db.Float):
                return "float"
            else:
                return "string"

        # Get column names and types
        column_types = {
            column.name: get_standard_type(column.type) for column in table.columns
        }

        # Exclude sensitive columns
        EXCLUDED_COLUMNS = [
            "id_user",
            "id_finder",
            "fundorte_id",
            "beschreibung_id",
            "dat_fund_bis",
            "fo_beleg",
            "bearb_id",
            "ablage",
        ]
        columns_with_excluded = columns.copy()
        columns = [col for col in columns if col not in EXCLUDED_COLUMNS]
        column_types = {col: column_types[col] for col in columns}

        # Convert results to list of lists
        data = [
            [
                getattr(row, col)
                for col in columns_with_excluded
                if col not in EXCLUDED_COLUMNS
            ]
            for row in results
        ]

        return jsonify(
            {
                "columns": columns,
                "data": data,
                "column_types": column_types,
                "non_editable_fields": NON_EDITABLE_FIELDS.get("all_data_view", []),
                "total_items": total_items,
            }
        )
    except Exception as e:
        current_app.logger.exception(f"Error in get_table_data: {str(e)}")
        return jsonify(
            {"error": f"An error occurred while fetching table data: {str(e)}"}
        ), 500


@admin.route("/admin/update_cell", methods=["POST"])
@reviewer_required
def update_cell():
    data = request.json
    if data is None:
        return jsonify({"error": "Invalid request"}), 400
    table_name = data["table"]
    column_name = data["column"]
    id_value = data["meldungen_id"]
    new_value = data["value"]

    if table_name != "all_data_view":
        return jsonify({"error": "Only all_data_view is supported"}), 403

    if (
        table_name in NON_EDITABLE_FIELDS
        and column_name in NON_EDITABLE_FIELDS[table_name]
    ):
        return jsonify({"error": "This field is not editable"}), 403

    try:
        # Find the original table and column
        original_table, original_column = find_original_table_and_column(column_name)
        if not original_table or not original_column:
            return jsonify({"error": "Unable to find original table and column"}), 400

        # Fetch the corresponding row from all_data_view
        all_data_row = db.session.scalar(
            select(TblAllData).where(TblAllData.meldungen_id == id_value)
        )
        if not all_data_row:
            return jsonify({"error": "Record not found"}), 404

        if original_table == TblUsers:
            user_db_id = all_data_row.id_user
            if not user_db_id:
                return jsonify({"error": "User ID not found in the record"}), 400
            stmt = (
                update(original_table)
                .where(original_table.id == user_db_id)
                .values(**{original_column: new_value})
            )
        elif original_table == TblFundorte:
            fundorte_id = all_data_row.fundorte_id
            if not fundorte_id:
                return jsonify({"error": "Fundorte ID not found in the record"}), 400

            # Validate and normalize coordinates before storing
            if original_column in ["latitude", "longitude"]:
                is_valid, normalized_value, error_msg = (
                    validate_and_normalize_coordinate(new_value, original_column)
                )
                if not is_valid:
                    return jsonify({"error": error_msg}), 400
                new_value = normalized_value

            stmt = (
                update(original_table)
                .where(original_table.id == fundorte_id)
                .values(**{original_column: new_value})
            )
        elif original_table == TblFundortBeschreibung:
            beschreibung_id = all_data_row.beschreibung_id
            if not beschreibung_id:
                return jsonify(
                    {"error": "Beschreibung ID not found in the record"}
                ), 400
            stmt = (
                update(original_table)
                .where(original_table.id == beschreibung_id)
                .values(**{original_column: new_value})
            )
        else:
            # Update TblMeldungen using meldungen_id
            stmt = (
                update(original_table)
                .where(original_table.id == id_value)
                .values(**{original_column: new_value})
            )

        # Execute the update
        result = db.session.execute(stmt)

        if result.rowcount == 0:
            return jsonify({"error": "Record not found"}), 404

        # If coordinates were updated, recalculate AMT and MTB
        if column_name in ["latitude", "longitude"] and original_table == TblFundorte:
            fundort = db.session.get(TblFundorte, fundorte_id)
            recalculate_amt_mtb(fundort)

        # Handle dat_fund_von changes - move images to new date folder
        if column_name == "dat_fund_von" and table_name == "all_data_view":
            image_update_result = update_report_image_date(id_value, new_value)
            if image_update_result[1] != 200:
                # Rollback database change if image move failed
                db.session.rollback()
                error_msg = image_update_result[0].get("error", "Failed to move image")
                return jsonify({"error": f"Date update failed: {error_msg}"}), 500
            elif image_update_result[0].get("status") == "success":
                current_app.logger.info(
                    f"Moved image for report {id_value} from {image_update_result[0].get('old_path')} "
                    f"to {image_update_result[0].get('new_path')}"
                )

        db.session.commit()

        # Refresh materialized view after update
        ad.refresh_materialized_view(db)
        session["last_updated_all_data_view"] = datetime.now()

        return jsonify({"success": True})

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error in update_cell: {str(e)}")
        errmsg = jsonify({"error": f"Error while updating the cell: {str(e)}"})
        return errmsg, 500


def find_original_table_and_column(column_name):
    table_column_mapping = {
        "meldungen_id": (TblMeldungen, "id"),
        "deleted": (TblMeldungen, "deleted"),
        "dat_fund_von": (TblMeldungen, "dat_fund_von"),
        "dat_fund_bis": (TblMeldungen, "dat_fund_bis"),
        "dat_meld": (TblMeldungen, "dat_meld"),
        "dat_bear": (TblMeldungen, "dat_bear"),
        "bearb_id": (TblMeldungen, "bearb_id"),
        "tiere": (TblMeldungen, "tiere"),
        "art_m": (TblMeldungen, "art_m"),
        "art_w": (TblMeldungen, "art_w"),
        "art_n": (TblMeldungen, "art_n"),
        "art_o": (TblMeldungen, "art_o"),
        "art_f": (TblMeldungen, "art_f"),
        "fo_zuordnung": (TblMeldungen, "fo_zuordnung"),
        "fo_quelle": (TblMeldungen, "fo_quelle"),
        "fo_beleg": (TblMeldungen, "fo_beleg"),
        "anm_melder": (TblMeldungen, "anm_melder"),
        "anm_bearbeiter": (TblMeldungen, "anm_bearbeiter"),
        "plz": (TblFundorte, "plz"),
        "ort": (TblFundorte, "ort"),
        "strasse": (TblFundorte, "strasse"),
        "kreis": (TblFundorte, "kreis"),
        "land": (TblFundorte, "land"),
        "amt": (TblFundorte, "amt"),
        "mtb": (TblFundorte, "mtb"),
        "longitude": (TblFundorte, "longitude"),
        "latitude": (TblFundorte, "latitude"),
        "ablage": (TblFundorte, "ablage"),
        "beschreibung": (TblFundortBeschreibung, "beschreibung"),
        "user_id": (TblUsers, "user_id"),
        "user_name": (TblUsers, "user_name"),
        "user_kontakt": (TblUsers, "user_kontakt"),
    }
    return table_column_mapping.get(column_name, (None, None))
