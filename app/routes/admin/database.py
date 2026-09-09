"""Superuser table browser over the alldata materialized view."""

from datetime import datetime, timedelta
import os
from pathlib import Path
import shutil

from flask import (
    current_app,
    jsonify,
    render_template,
    request,
    session,
)
from sqlalchemy import func, select, update
from sqlalchemy.exc import SQLAlchemyError

import app.database.alldata as ad
from flask_login import current_user

from app.auth import reviewer_required
from app.database.models import (
    TblAllData,
    TblFundorte,
    TblMeldungen,
    TblUsers,
)
from app.extensions import db
from app.routes.admin.blueprint import admin
from app.routes.admin.common import _inspect_sqlalchemy, recalculate_amt_mtb
from app.routes.backup import available_backup_years
from app.tools.coordinate_validation import validate_and_normalize_coordinate
from app.tools.report_images import build_upload_filename, ensure_upload_dir


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


def _maybe_refresh_alldata_view(*, force: bool = False) -> None:
    """Refresh the alldata materialized view if stale (>1 min) or forced."""
    if not force:
        last_updated = session.get("last_updated_all_data_view")
        # Handle timezone info that Flask session serialization may add
        if last_updated and hasattr(last_updated, "tzinfo") and last_updated.tzinfo:
            last_updated = last_updated.replace(tzinfo=None)
        now = datetime.now()
        if last_updated is not None and (now - last_updated <= timedelta(minutes=1)):
            return
    else:
        now = datetime.now()
    ad.refresh_materialized_view(db)
    session["last_updated_all_data_view"] = now


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
    # Extract location and user id from filename
    filename_parts = old_filename.rsplit("-", 2)
    if len(filename_parts) != 3:
        raise ValueError(f"Invalid filename format: {old_filename}")

    location = filename_parts[0]
    usrid_with_ext = filename_parts[2]
    usrid = usrid_with_ext.replace(".webp", "")

    new_dir_path = ensure_upload_dir(base_dir, new_date_obj)
    new_file_path = new_dir_path / build_upload_filename(location, usrid, new_date_obj)

    # Skip if source and destination are the same
    if str(old_image_path) == str(new_file_path):
        return {"status": "no_change"}

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
    _maybe_refresh_alldata_view()
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
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)
        search = request.args.get("search", "")
        search_type = request.args.get("search_type", "full_text")
        sort_column = request.args.get("sort_column", "meldungen_id")
        sort_direction = request.args.get("sort_direction", "asc")

        _maybe_refresh_alldata_view()

        # Get the table object - we only work with TblAllData now
        table = TblAllData.__table__

        columns = [column.name for column in table.columns]

        # Validate sort_column to prevent SQL injection
        if sort_column not in columns:
            sort_column = "meldungen_id"

        # Create a filtered select statement first; count and paginated data
        # should come from the same search conditions.
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
                ts_query = func.websearch_to_tsquery("german", search)
                meldungen_tbl = _inspect_sqlalchemy(TblMeldungen).mapper.local_table
                stmt = stmt.join(
                    meldungen_tbl, table.c.meldungen_id == meldungen_tbl.c.id
                ).where(meldungen_tbl.c.search_vector.op("@@")(ts_query))

        total_items = db.session.scalar(
            select(func.count()).select_from(stmt.order_by(None).subquery())
        )

        # Apply sorting
        if sort_direction == "asc":
            stmt = stmt.order_by(table.c[sort_column].asc())
        else:
            stmt = stmt.order_by(table.c[sort_column].desc())

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
                "editable_fields": list(EDITABLE_FIELDS),
                "total_items": total_items,
            }
        )
    except Exception as e:
        current_app.logger.exception(f"Error in get_table_data: {str(e)}")
        return jsonify({"error": "An error occurred while fetching table data"}), 500


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

    try:
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
                is_valid, normalized_value, error_msg = (
                    validate_and_normalize_coordinate(new_value, column_name)
                )
                if not is_valid:
                    return jsonify({"error": error_msg}), 400
                new_value = normalized_value

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
                    f"Moved image for report {id_value} from {image_update_result.get('old_path')} "
                    f"to {image_update_result.get('new_path')}"
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
                except Exception:
                    current_app.logger.critical(
                        f"Could not revert image move for report {id_value} after "
                        f"commit failure: file stuck at "
                        f"{image_update_result['new_path']}, "
                        f"DB expects {image_update_result['old_path']}"
                    )
            raise

        # The edit is already committed; a projection failure must not make the
        # client retry an update that actually succeeded.
        try:
            _maybe_refresh_alldata_view(force=True)
        except Exception:
            db.session.rollback()
            current_app.logger.exception(
                "Cell updated, but failed to refresh all_data_view"
            )

        return jsonify({"success": True})

    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(f"Error in update_cell: {str(e)}")
        errmsg = jsonify({"error": "Error while updating the cell"})
        return errmsg, 500
