"""Excel export of the reviewer's current filter selection."""

from datetime import datetime
from io import BytesIO
import tempfile

import xlsxwriter
from flask import abort, send_file
from sqlalchemy import func

from app.auth import reviewer_required
from app.database.models import ReportStatus
from app.extensions import db
from app.routes.admin.blueprint import admin
from app.routes.admin.filters import get_filtered_query, get_reviewer_filter_args


def _export_date(value) -> str:
    return value.strftime("%d.%m.%Y") if value else ""


# One row per spreadsheet column: header, width, and how to read the value off a
# Meldung.
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

# Reporters type the text cells, so they stay text: no formulas, no hyperlinks.
AS_TYPED = {"strings_to_formulas": False, "strings_to_urls": False}

EXPORT_FILENAMES = {
    "all": ("Alle_Meldungen", "all"),
    "accepted": ("Akzeptierte_Meldungen", "bearbeitet"),
    "non_accepted": ("Nicht_akzeptierte_Meldungen", "offen"),
}


@admin.route("/admin/export/xlsx/<string:value>")
@reviewer_required
def export_data(value):
    """Send the selected reports as an Excel file."""
    current_time = datetime.now().strftime("%d.%m.%Y_%H%M")

    if value in EXPORT_FILENAMES:
        stem, filter_status = EXPORT_FILENAMES[value]
        filename = f"{stem}_{current_time}.xlsx"
        stmt = get_filtered_query(filter_status=filter_status)
    elif value == "searched":
        filename = f"Suchergebnisse_{current_time}.xlsx"
        stmt = get_filtered_query(**get_reviewer_filter_args())
    else:
        abort(404, description="Resource not found")

    row_count = db.session.scalar(stmt.with_only_columns(func.count()).order_by(None))
    # Large exports stream into an unnamed temp file, which send_file closes
    # and the OS then deletes; small ones build in memory.
    use_large_mode = row_count > LARGE_EXPORT_THRESHOLD
    if use_large_mode:
        output = tempfile.TemporaryFile()
        workbook = xlsxwriter.Workbook(output, {"constant_memory": True, **AS_TYPED})
    else:
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True, **AS_TYPED})

    worksheet = workbook.add_worksheet("Daten")
    header_format = workbook.add_format(
        {"bold": True, "bg_color": "#4472C4", "font_color": "white", "border": 1}
    )
    for col_idx, (header, width, _) in enumerate(EXPORT_COLUMNS):
        worksheet.write(0, col_idx, header, header_format)
        worksheet.set_column(col_idx, col_idx, width)

    # yield_per streams in batches; it allows the many-to-one eager loads here.
    reports = db.session.scalars(stmt.execution_options(yield_per=1000))
    last_row = 0
    for last_row, meldung in enumerate(reports, start=1):
        for col_idx, (_, _, value_of) in enumerate(EXPORT_COLUMNS):
            worksheet.write(last_row, col_idx, value_of(meldung))

    if not use_large_mode and last_row:
        column_settings = [{"header": header} for header, _, _ in EXPORT_COLUMNS]
        worksheet.add_table(
            0,
            0,
            last_row,
            len(EXPORT_COLUMNS) - 1,
            {"columns": column_settings, "style": "Table Style Medium 9"},
        )
    worksheet.freeze_panes(1, 0)
    workbook.close()

    output.seek(0)
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename,
    )
