"""Excel export of the reviewer's current filter selection."""

from datetime import datetime
from io import BytesIO
from pathlib import Path
import tempfile

import xlsxwriter
from flask import abort, current_app, send_file
from sqlalchemy import func

from app.auth import reviewer_required
from app.database.models import ReportStatus
from app.extensions import db
from app.routes.admin.blueprint import admin
from app.routes.admin.filters import get_filtered_query, get_reviewer_filter_args


def _export_date(value) -> str:
    return value.strftime("%d.%m.%Y") if value else ""


# One row per spreadsheet column: header, width, and how to read the value off a
# Meldung. Header text and value used to live in two separate lists indexed by
# hand, where inserting a column silently shifted every value after it.
EXPORT_COLUMNS = (
    ("ID", 8, lambda m: m.id),
    ("Status", 12, lambda m: ReportStatus.get_display_names(m.statuses or [])),
    ("Fund-Datum", 12, lambda m: _export_date(m.dat_fund_von)),
    ("Melde-Datum", 12, lambda m: _export_date(m.dat_meld)),
    ("Bearbeitungs-Datum", 18, lambda m: _export_date(m.dat_bear)),
    ("Anzahl Tiere", 12, lambda m: m.tiere),
    ("Männchen", 10, lambda m: m.art_m),
    ("Weibchen", 10, lambda m: m.art_w),
    ("Nymphen", 10, lambda m: m.art_n),
    ("Ootheken", 10, lambda m: m.art_o),
    ("Andere", 10, lambda m: m.art_f),
    ("Fundort-Quelle", 14, lambda m: m.fo_quelle),
    ("Anmerkung Melder", 30, lambda m: m.anm_melder),
    ("Anmerkung Bearbeiter", 30, lambda m: m.anm_bearbeiter),
    ("PLZ", 8, lambda m: m.fundort.plz),
    ("Ort", 20, lambda m: m.fundort.ort),
    ("Straße", 25, lambda m: m.fundort.strasse),
    ("Kreis", 20, lambda m: m.fundort.kreis),
    ("Land", 15, lambda m: m.fundort.land),
    ("Amt", 25, lambda m: m.fundort.amt),
    ("MTB", 8, lambda m: m.fundort.mtb),
    ("Längengrad", 12, lambda m: m.fundort.longitude),
    ("Breitengrad", 12, lambda m: m.fundort.latitude),
    ("Beschreibung", 30, lambda m: m.fundort.location_type.beschreibung),
    ("Melder Name", 20, lambda m: m.reporter_link.reporter.user_name),
    ("Melder Kontakt", 25, lambda m: m.reporter_link.reporter.user_kontakt),
    ("Bearbeiter", 20, lambda m: m.approver.user_name if m.approver else ""),
)

# Above this many rows, xlsxwriter runs in constant_memory mode against a temp
# file. That mode cannot add a table, so the formatting below is skipped.
LARGE_EXPORT_THRESHOLD = 5000

EXPORT_FILENAMES = {
    "all": ("Alle_Meldungen", "all"),
    "accepted": ("Akzeptierte_Meldungen", "bearbeitet"),
    "non_accepted": ("Nicht_akzeptierte_Meldungen", "offen"),
}


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
        filter_args = get_reviewer_filter_args()

        # Get filtered select statement based on export type
        if value in EXPORT_FILENAMES:
            stem, filter_status = EXPORT_FILENAMES[value]
            filename = f"{stem}_{current_time}.xlsx"
            stmt = get_filtered_query(filter_status=filter_status)
        elif value == "searched":
            filename = f"Suchergebnisse_{current_time}.xlsx"
            stmt = get_filtered_query(**filter_args)
        else:
            abort(404, description="Resource not found")

        # First pass: Get count for choosing export mode.
        # Build a lightweight count query reusing the same JOINs/WHERE but no ORM options.
        count_stmt = stmt.options().with_only_columns(func.count()).order_by(None)
        row_count = db.session.scalar(count_stmt) or 0

        # Approver is eagerly loaded via outerjoin in get_filtered_query().

        # Use temp file for large exports, BytesIO for small ones
        use_large_mode = row_count > LARGE_EXPORT_THRESHOLD
        output_path: str | None = None
        output: BytesIO | None = None
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

        # Write headers and set column widths
        for col_idx, (header, width, _) in enumerate(EXPORT_COLUMNS):
            worksheet.write(0, col_idx, header, header_format)
            worksheet.set_column(col_idx, col_idx, width)

        # Stream data using yield_per for memory efficiency.
        # contains_eager() on scalar (uselist=False) relationships is compatible
        # with yield_per — no collection loading, so no dedup needed.
        # Note: .unique() is NOT compatible with yield_per in SQLAlchemy ORM mode.
        streaming_stmt = stmt.execution_options(yield_per=1000)
        result = db.session.scalars(streaming_stmt)

        row_idx = 1
        for meldung in result:
            for col_idx, (_, _, value_of) in enumerate(EXPORT_COLUMNS):
                worksheet.write(row_idx, col_idx, value_of(meldung))
            row_idx += 1

        # Add table formatting only for small exports (constant_memory can't use tables)
        if not use_large_mode and row_idx > 1:
            column_settings = [{"header": header} for header, _, _ in EXPORT_COLUMNS]
            worksheet.add_table(
                0,
                0,
                row_idx - 1,
                len(EXPORT_COLUMNS) - 1,
                {"columns": column_settings, "style": "Table Style Medium 9"},
            )

        # Freeze header row
        worksheet.freeze_panes(1, 0)

        workbook.close()

        # Send the file
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if use_large_mode:
            # Send temp file and clean up after
            assert output_path is not None
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
            assert output is not None
            output.seek(0)
            return send_file(
                output, mimetype=mime, as_attachment=True, download_name=filename
            )
    except Exception:
        current_app.logger.exception("Error in export_data")
        abort(500)
