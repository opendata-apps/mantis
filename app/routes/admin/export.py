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
from app.routes.admin.filters import get_filtered_query, _get_reviewer_filter_args


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
        filter_args = _get_reviewer_filter_args()

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
            stmt = get_filtered_query(**filter_args)
        else:
            abort(404, description="Resource not found")

        # First pass: Get count for choosing export mode.
        # Build a lightweight count query reusing the same JOINs/WHERE but no ORM options.
        count_stmt = stmt.options().with_only_columns(func.count()).order_by(None)
        row_count = db.session.scalar(count_stmt) or 0

        # Threshold for using memory-optimized mode (constant_memory)
        # Below this, use standard mode with table formatting
        LARGE_EXPORT_THRESHOLD = 5000

        # Approver is eagerly loaded via outerjoin in get_filtered_query().

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
        for col_idx, (col_name, col_width) in enumerate(columns):
            worksheet.write(0, col_idx, col_name, header_format)
            worksheet.set_column(col_idx, col_idx, col_width)

        # Stream data using yield_per for memory efficiency.
        # contains_eager() on scalar (uselist=False) relationships is compatible
        # with yield_per — no collection loading, so no dedup needed.
        # Note: .unique() is NOT compatible with yield_per in SQLAlchemy ORM mode.
        streaming_stmt = stmt.execution_options(yield_per=1000)
        result = db.session.scalars(streaming_stmt)

        row_idx = 1
        for meldung in result:
            fundort = meldung.fundort
            beschreibung = fundort.location_type
            user = meldung.reporter_link.reporter

            # Write row data directly (no intermediate dict/list)
            worksheet.write(row_idx, 0, meldung.id)
            worksheet.write(
                row_idx, 1, ReportStatus.get_display_names(meldung.statuses or [])
            )
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
            # Approver (eagerly loaded via outerjoin)
            worksheet.write(
                row_idx,
                26,
                meldung.approver.user_name if meldung.approver else "",
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
