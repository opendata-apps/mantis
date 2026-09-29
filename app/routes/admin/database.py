"""Superuser table browser over the alldata view."""

import os
import shutil
from datetime import datetime
from pathlib import Path

from flask import (
    abort,
    current_app,
    make_response,
    render_template,
    request,
)
from flask_login import current_user
from sqlalchemy import false, func, select
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
from app.tools.coordinate_validation import normalize_location_input
from app.tools.fts import prefix_tsquery
from app.tools.location_enrichment import recalculate_amt_mtb
from app.tools.report_images import ensure_upload_dir

GRID_PAGE_SIZE = 50

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


def grid_statement(search, search_type, sort_column, direction):
    """The alldata rows matching the search, in a stable order."""
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
    sort = TblAllData.__table__.c[sort_column]
    return stmt.order_by(
        sort.asc() if direction == "asc" else sort.desc(), TblAllData.meldungen_id
    )


@admin.route("/alldata")
@reviewer_required
def database_view():
    columns = [
        column
        for column in TblAllData.__table__.columns
        if column.name not in HIDDEN_COLUMNS
    ]
    sort = request.args.get("sort", "meldungen_id")
    if sort not in TblAllData.__table__.c:
        sort = "meldungen_id"
    # The URL query is the grid state: search, sort and the page being loaded.
    state = {
        "q": request.args.get("q", ""),
        "search_type": request.args.get("search_type", "full_text"),
        "sort": sort,
        "dir": "desc" if request.args.get("dir") == "desc" else "asc",
    }
    pagination = db.paginate(
        grid_statement(state["q"], state["search_type"], state["sort"], state["dir"]),
        per_page=GRID_PAGE_SIZE,
        error_out=False,
    )
    grid = {
        "columns": columns,
        "pagination": pagination,
        "state": state,
        "editable": EDITABLE_FIELDS,
    }
    if not request.headers.get("HX-Request"):
        return render_template(
            "admin/database.html",
            user_id=current_user.user_id,
            backup_years=available_backup_years(),
            **grid,
        )
    template = "_grid_rows.html" if pagination.page > 1 else "_grid.html"
    return render_template(f"admin/partials/{template}", **grid)


def render_cell_editor(report_id, column, value, error=None):
    column_type = TblAllData.__table__.c[column].type.python_type.__name__
    return render_template(
        "admin/partials/_cell_editor.html",
        report_id=report_id,
        column=column,
        column_type=column_type,
        value=cell_text(value),
        error=error,
    )


@admin.app_template_filter("cell_text")
def cell_text(value):
    if value is None:
        return ""
    if isinstance(value, list):
        return ",".join(value)
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


@admin.get("/admin/cell/<int:report_id>/<column>")
@reviewer_required
def cell_editor(report_id, column):
    if column not in EDITABLE_FIELDS:
        abort(403, "This field is not editable")
    row = db.get_or_404(TblAllData, report_id)
    return render_cell_editor(report_id, column, getattr(row, column))


@admin.post("/admin/cell/<int:report_id>/<column>")
@reviewer_required
def update_cell(report_id, column):
    """Save one cell. A rejected value re-renders the editor with the message."""
    original_table = EDITABLE_FIELDS.get(column)
    if original_table is None:
        abort(403, "This field is not editable")
    new_value = request.form["value"]

    def rejected(message):
        return render_cell_editor(report_id, column, new_value, message)

    report = db.get_or_404(TblMeldungen, report_id)

    if TblAllData.__table__.c[column].type.python_type is int:
        try:
            new_value = int(new_value)
        except ValueError:
            return rejected("Enter a whole number.")

    if original_table == TblUsers:
        link = report.reporter_link
        target = link.reporter if link else None
        if not target:
            abort(400, "User ID not found in the record")
    elif original_table == TblFundorte:
        target = report.fundort
        if not target:
            abort(400, "Fundorte ID not found in the record")
        new_value, error_msg = normalize_location_input(column, new_value)
        if error_msg:
            return rejected(error_msg)
    else:
        target = report

    setattr(target, column, new_value)

    if column in ("latitude", "longitude"):
        recalculate_amt_mtb(target)

    # Handle dat_fund_von changes - move images to new date folder
    image_update_result = None
    if column == "dat_fund_von":
        try:
            image_update_result = update_report_image_date(report_id, new_value)
        except (LookupError, FileNotFoundError, ValueError, OSError) as exc:
            db.session.rollback()
            return rejected(f"Date update failed: {exc}")

        if image_update_result.get("status") == "success":
            current_app.logger.info(
                "Moved image for report %s from %s to %s",
                report_id,
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
                    report_id,
                    image_update_result["new_path"],
                    image_update_result["old_path"],
                )
        raise

    # The cell replaces itself; an empty dialog shell swapped in out of band closes the editor.
    response = make_response(
        render_template(
            "admin/partials/_cell.html",
            row=db.session.get(TblAllData, report_id),
            column=TblAllData.__table__.c[column],
            editable=EDITABLE_FIELDS,
        )
        + render_template("admin/partials/_cell_dialog.html", oob=True)
    )
    response.headers["HX-Retarget"] = f"#cell-{report_id}-{column}"
    response.headers["HX-Reswap"] = "outerHTML"
    return response
