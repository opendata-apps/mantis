"""Superuser table browser over the alldata view."""

import os
import shutil
from datetime import datetime
from pathlib import Path

from flask import (
    current_app,
    jsonify,
    render_template,
    request,
)
from flask_login import current_user
from sqlalchemy import false, func, select, update
from sqlalchemy.exc import SQLAlchemyError

from app.auth import reviewer_required
from app.database.models import (
    TblAllData,
    TblFundorte,
    TblMeldungen,
    TblUsers,
)
from app.extensions import db
from app.routes.admin.blueprint import admin
from app.routes.backup import available_backup_years
from app.tools.coordinate_validation import validate_coordinate
from app.tools.fts import prefix_tsquery
from app.tools.location_enrichment import recalculate_amt_mtb
from app.tools.postal_code import is_valid_plz
from app.tools.report_images import ensure_upload_dir

EDITABLE_FIELDS = {
    "dat_fund_von": TblMeldungen,
    "dat_meld": TblMeldungen,
    "dat_bear": TblMeldungen,
    "tiere": TblMeldungen,
    "art_m": TblMeldungen,
    "art_w": TblMeldungen,
    "art_n": TblMeldungen,
    "art_o": TblMeldungen,
    "art_f": TblMeldungen,
    "fo_quelle": TblMeldungen,
    "anm_melder": TblMeldungen,
    "anm_bearbeiter": TblMeldungen,
    "plz": TblFundorte,
    "ort": TblFundorte,
    "strasse": TblFundorte,
    "kreis": TblFundorte,
    "land": TblFundorte,
    "amt": TblFundorte,
    "mtb": TblFundorte,
    "longitude": TblFundorte,
    "latitude": TblFundorte,
    "user_name": TblUsers,
    "user_kontakt": TblUsers,
}

# Internal ids and fields the grid does not show.
HIDDEN_COLUMNS = frozenset(
    {
        "id_user",
        "id_finder",
        "fundorte_id",
        "beschreibung_id",
        "dat_fund_bis",
        "fo_beleg",
        "bearb_id",
        "ablage",
    }
)


def update_report_image_date(report_id, new_date):
    """Update the image location when dat_fund_von changes"""
    # Handle both string and datetime objects
    if isinstance(new_date, str):
        new_date_obj = datetime.strptime(new_date, "%Y-%m-%d")
    else:
        new_date_obj = new_date

    # Fetch the report
    report = db.session.get(TblMeldungen, report_id)
    if not report:
        raise LookupError("Report not found")

    fundorte_record = report.fundort
    if not fundorte_record or not fundorte_record.ablage:
        # No image to move
        return {"status": "no_image"}

    base_dir = Path(current_app.config["UPLOAD_FOLDER"])
    old_image_path = base_dir / fundorte_record.ablage

    # Check if the old image file exists
    if not old_image_path.exists():
        raise FileNotFoundError(f"Image file not found: {fundorte_record.ablage}")

    old_dir, old_filename = os.path.split(old_image_path)
    new_dir_path = ensure_upload_dir(base_dir, new_date_obj)
    new_file_path = new_dir_path / old_filename

    # Skip if source and destination are the same
    if str(old_image_path) == str(new_file_path):
        return {"status": "no_change"}

    if new_file_path.exists():
        raise FileExistsError(f"Target image already exists: {new_file_path}")

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

    except OSError as e:
        raise OSError(f"Failed to move file: {e}") from e

    # Update the path in fundorte table
    fundorte_record.ablage = str(new_file_path.relative_to(base_dir))
    db.session.flush()

    return {
        "status": "success",
        "old_path": str(old_image_path),
        "new_path": str(new_file_path),
    }


@admin.route("/alldata")
@reviewer_required
def database_view():
    return render_template(
        "admin/database.html",
        user_id=current_user.user_id,
        backup_years=available_backup_years(),
    )


@admin.route("/admin/get_table_data/<table_name>")
@reviewer_required
def get_table_data(table_name):
    if table_name != "all_data_view":
        return jsonify({"error": "Only all_data_view is available"}), 403
    search = request.args.get("search", "")
    search_type = request.args.get("search_type", "full_text")
    sort_column = request.args.get("sort_column", "meldungen_id")
    sort_direction = request.args.get("sort_direction", "asc")

    table = TblAllData.__table__
    columns = [column for column in table.columns if column.name not in HIDDEN_COLUMNS]
    if sort_column not in table.c:
        sort_column = "meldungen_id"

    stmt = select(TblAllData)
    if search and search_type == "id":
        try:
            stmt = stmt.where(TblAllData.meldungen_id == int(search))
        except ValueError:
            stmt = stmt.where(false())
    elif search:
        ts_query = func.to_tsquery("german", prefix_tsquery(search))
        stmt = stmt.join(TblMeldungen, TblAllData.meldungen_id == TblMeldungen.id)
        stmt = stmt.where(TblMeldungen.search_vector.op("@@")(ts_query))

    # meldungen_id breaks ties; without a unique order, OFFSET pages overlap.
    sort = table.c[sort_column]
    stmt = stmt.order_by(
        sort.asc() if sort_direction == "asc" else sort.desc(), TblAllData.meldungen_id
    )
    # db.paginate reads ?page itself.
    pagination = db.paginate(
        stmt,
        per_page=request.args.get("per_page", 10, type=int),
        max_per_page=100,
        error_out=False,
    )

    return jsonify(
        {
            "columns": [column.name for column in columns],
            "data": [
                [getattr(row, column.name) for column in columns]
                for row in pagination.items
            ],
            # "int", "float", "date", "str" or "list"; the grid picks its editor by it.
            "column_types": {
                column.name: column.type.python_type.__name__ for column in columns
            },
            "editable_fields": list(EDITABLE_FIELDS),
            "total_items": pagination.total,
        }
    )


@admin.route("/admin/update_cell", methods=["POST"])
@reviewer_required
def update_cell():
    data = request.json
    if data is None:
        return jsonify({"error": "Invalid request"}), 400

    try:
        column_name = data["column"]
        raw_id_value = data["meldungen_id"]
        new_value = data["value"]
    except KeyError as exc:
        return jsonify({"error": f"Missing field: {exc.args[0]}"}), 400

    if isinstance(raw_id_value, bool):
        return jsonify({"error": "Invalid report ID"}), 400
    try:
        id_value = int(raw_id_value)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid report ID"}), 400

    original_table = EDITABLE_FIELDS.get(column_name)
    if original_table is None:
        return jsonify({"error": "This field is not editable"}), 403

    # Fetch the corresponding row from all_data_view
    all_data_row = db.session.scalar(
        select(TblAllData).where(TblAllData.meldungen_id == id_value)
    )
    if not all_data_row:
        return jsonify({"error": "Record not found"}), 404

    fundorte_id = None
    if original_table == TblUsers:
        user_db_id = all_data_row.id_user
        if not user_db_id:
            return jsonify({"error": "User ID not found in the record"}), 400
        stmt = (
            update(original_table)
            .where(original_table.id == user_db_id)
            .values(**{column_name: new_value})
        )
    elif original_table == TblFundorte:
        fundorte_id = all_data_row.fundorte_id
        if not fundorte_id:
            return jsonify({"error": "Fundorte ID not found in the record"}), 400

        # Validate and normalize coordinates before storing
        if column_name in ["latitude", "longitude"]:
            normalized_value, error_msg = validate_coordinate(new_value, column_name)
            if error_msg:
                return jsonify({"error": error_msg}), 400
            new_value = normalized_value

        if column_name == "plz":
            if new_value in (None, ""):
                new_value = None
            elif not is_valid_plz(new_value):
                return jsonify({"error": "Invalid ZIP code"}), 400

        stmt = (
            update(original_table)
            .where(original_table.id == fundorte_id)
            .values(**{column_name: new_value})
        )
    else:
        stmt = (
            update(original_table)
            .where(original_table.id == id_value)
            .values(**{column_name: new_value})
        )

    # Execute the update
    result = db.session.execute(stmt)

    if getattr(result, "rowcount", None) == 0:
        return jsonify({"error": "Record not found"}), 404

    # If coordinates were updated, recalculate AMT and MTB
    if (
        column_name in ["latitude", "longitude"]
        and original_table == TblFundorte
        and fundorte_id is not None
    ):
        fundort = db.session.get(TblFundorte, fundorte_id)
        recalculate_amt_mtb(fundort)

    # Handle dat_fund_von changes - move images to new date folder
    image_update_result = None
    if column_name == "dat_fund_von":
        try:
            image_update_result = update_report_image_date(id_value, new_value)
        except (LookupError, FileNotFoundError, ValueError, OSError) as exc:
            db.session.rollback()
            return jsonify({"error": f"Date update failed: {exc}"}), 500

        if image_update_result.get("status") == "success":
            current_app.logger.info(
                "Moved image for report %s from %s to %s",
                id_value,
                image_update_result.get("old_path"),
                image_update_result.get("new_path"),
            )

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        # Compensate the filesystem change if the DB commit failed — otherwise
        # the DB would roll back to the old `ablage` while the file is already
        # at the new location, leaving the image inaccessible to /admin/images.
        if image_update_result and image_update_result.get("status") == "success":
            try:
                shutil.move(
                    image_update_result["new_path"],
                    image_update_result["old_path"],
                )
            except OSError:
                current_app.logger.critical(
                    "Could not revert image move for report %s after commit failure: file stuck at %s, DB expects %s",
                    id_value,
                    image_update_result["new_path"],
                    image_update_result["old_path"],
                )
        raise

    return jsonify({"success": True})
