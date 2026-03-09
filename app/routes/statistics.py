from flask import Blueprint
from flask import render_template, request, current_app
from flask import session
from markupsafe import escape
from sqlalchemy import func, select
from sqlalchemy import cast, String
from sqlalchemy import literal_column
from app import db
from app.database.models import TblAemterCoordinaten
from app.auth import reviewer_required
from app.tools.gen_messtisch_svg import create_measure_sheet
from app.database.models import TblFundorte, TblMeldungen
from app.database.models import TblUserFeedback, ReportStatus
from datetime import date, datetime, timedelta
from app.database.feedback_type import FeedbackSource
from app.database.ags import (
    BUNDESLAENDER,
    BERLIN_BEZIRKE,
    BRANDENBURG_LANDKREISE,
    build_gesamt_template,
)

stats = Blueprint("statistics", __name__)


def _gender_sum_columns():
    """Return the common aggregation columns for gender/stage statistics.

    Used by stats_mtb, stats_geschlecht,
    stats_amt, stats_laender, stats_bundesland.
    """
    return [
        func.sum(func.coalesce(TblMeldungen.art_m, 0)).label("maennlich"),
        func.sum(func.coalesce(TblMeldungen.art_w, 0)).label("weiblich"),
        func.sum(func.coalesce(TblMeldungen.art_o, 0)).label("oothek"),
        func.sum(func.coalesce(TblMeldungen.art_n, 0)).label("nymphe"),
        func.sum(func.coalesce(TblMeldungen.art_f, 0)).label("andere"),
        func.sum(
            func.coalesce(TblMeldungen.art_m, 0)
            + func.coalesce(TblMeldungen.art_w, 0)
            + func.coalesce(TblMeldungen.art_o, 0)
            + func.coalesce(TblMeldungen.art_n, 0)
            + func.coalesce(TblMeldungen.art_f, 0)
        ).label("gesamt"),
    ]

list_of_stats = {
    "xxx": "Bitte eine Wahl treffen ...",
    "start": "Startseite/Filter",
    "geschlecht": "Entwicklungsstadium/Geschlecht",
    "meldungen_funddatum": "Meldungen: Funddatum",
    "meldungen_meldedatum": "Meldungen: Meldedatum",
    "meldungen_meld_fund": "Meldungen: Fund- und Meldedatum",
    "meldungen_mtb": "Grafik: Messtischblatt",
    "meldungen_amt": "Auswertung Amt/Gemeinde",
    "meldungen_laender": "Meldungen Bundesländer",
    "meldungen_brb": "Meldungen Brandenburg",
    "meldungen_berlin": "Meldungen Berlin",
    "meldungen_gesamt": "Alle Summen (Tabelle)",
    "meldungen_zeiten": "Meldezeiten",
    "feedback": "Feedback",
}


@stats.route("/statistik/ags", methods=["GET"])
def autocomplete_ags():
    q = request.args.get("ags_input", "").strip()
    if len(q) < 2:
        return ""

    stmt = (
        select(TblAemterCoordinaten.ags, TblAemterCoordinaten.gen)
        .where(
            (cast(TblAemterCoordinaten.ags, String).startswith(q))
            | (TblAemterCoordinaten.gen.ilike(f"{q}%"))
        )
        .order_by(TblAemterCoordinaten.gen)
        .limit(10)
    )

    rows = db.session.execute(stmt).all()
    return "".join(
        f"""
        <li
            class="suggestion"
            data-ags="{escape(ags)}"
            data-gen="{escape(gen)}"
        >
            <strong>{escape(ags)}</strong>: {escape(gen)}
        </li>
        """
        for ags, gen in rows
    )


def get_date_interval():
    "Calculate and format start and end date"

    now = datetime.now().isoformat()
    last_year = datetime.now() - timedelta(weeks=52)
    last_year = last_year.isoformat()
    start_date = request.form.get("dateFrom",
                                  session.get("date_from", last_year))
    end_date = request.form.get("dateTo", session.get("date_to", now))

    return (start_date[:10], end_date[:10])


@stats.route("/statistik", methods=["POST", "GET"])
@reviewer_required
def stats_start():
    "Startseite für alle Statistiken"

    session["date_from"], session["date_to"] = get_date_interval()
    session["ags"] = request.form.get("ags", session.get("ags", "")).strip()

    value = request.form.get("stats", "start")
    session["marker"] = value

    match value:
        case "geschlecht":
            return stats_geschlecht(marker=value)
        case "meldungen_meldedatum":
            return stats_bardiagram_datum(
                dbfields=["dat_meld"],
                page="stats-meldedatum.html",
                marker=value
            )
        case "meldungen_funddatum":
            return stats_bardiagram_datum(
                dbfields=["dat_fund_von"],
                page="stats-funddatum.html",
                marker=value
            )
        case "meldungen_meld_fund":
            return stats_bardiagram_datum(
                dbfields=["dat_fund_von", "dat_meld"],
                page="stats-meld-fund.html",
                marker=value,
            )
        case "meldungen_mtb":
            return stats_mtb(marker=value)
        case "meldungen_amt":
            return stats_amt(marker="meldungen_amt")
        case "meldungen_laender":
            return stats_laender(marker="meldungen_laender")
        case "meldungen_brb":
            return stats_bundesland(marker="meldungen_brb")
        case "meldungen_berlin":
            return stats_bundesland(marker="meldungen_berlin")
        case "meldungen_gesamt":
            return stats_gesamt(marker="meldungen_gesamt")
        case "meldungen_zeiten":
            return stats_daily_average(marker="meldungen_zeiten")
        case "feedback":
            return stats_feedback(
                marker="feedback",
                page="stats-feedback.html",
            )
        case "start":
            return render_template(
                "statistics/statistiken.html", menu=list_of_stats, marker=value
            )
        case _:
            return render_template(
                "statistics/statistiken.html", menu=list_of_stats, marker=value
            )


def stats_daily_average(marker="meldungen_zeiten"):
    """Get reports based on hours

    We are using timestamps included in image names
    (column »ablage« in table fundorte).
    """

    timestamp_substr = func.substring(TblFundorte.ablage, r'-([0-9]{14})-')
    timestamp_expr = func.to_timestamp(timestamp_substr, 'YYYYMMDDHH24MISS')
    hour_expr = func.extract("hour", timestamp_expr)

    date_from = date.fromisoformat(session["date_from"])
    date_to = date.fromisoformat(session["date_to"])

    stmt = (
        select(
            hour_expr.label("stunde"),
            func.count().label("anzahl_meldungen")
        )
        .join(TblMeldungen)
        .where(
            timestamp_substr.isnot(None),
            TblMeldungen.dat_fund_von >= date_from,
            TblMeldungen.dat_fund_von <= date_to,
            TblMeldungen.statuses.contains([ReportStatus.APPR.value]),
        )
        .where(TblFundorte.amt.like(f"{session['ags']}%"))
        .group_by(hour_expr)
        .order_by(hour_expr)
    )

    results = db.session.execute(stmt).all()

    daily = {
        "0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0,
        "7": 0, "8": 0, "9": 0, "10": 0, "11": 0, "12": 0, "13": 0,
        "14": 0, "15": 0, "16": 0, "17": 0, "18": 0, "19": 0,
        "20": 0, "21": 0, "22": 0, "23": 0
    }

    for row in results:
        daily[f"{int(row[0])}"] = row[1]

    return render_template(
        "statistics/stats-daily-average.html",
        menu=list_of_stats,
        daten=daily,
        marker=marker,
    )


def stats_mtb(marker):
    "Results as MTB (Messtischblatt-Raster)"

    art = request.form.get("typeInput", "all")
    typeInput = ["mtb", "maennlich", "weiblich", "oothek",
                 "nymphe", "andere", "all"]
    dbanswers = []
    stmt = (
        select(TblFundorte.mtb, *_gender_sum_columns())
        .join(TblMeldungen)
        .where(
            TblMeldungen.dat_fund_von >= date.fromisoformat(session["date_from"]),
            TblMeldungen.dat_fund_von <= date.fromisoformat(session["date_to"]),
            TblMeldungen.statuses.contains([ReportStatus.APPR.value]),
        )
        .where(TblFundorte.amt.like(f"{session['ags']}%"))
        .group_by(TblFundorte.mtb)
    )

    results = db.session.execute(stmt).all()
    idx = typeInput.index(art)

    for row in results[:]:
        if row[idx] > 0 and row[0] is not None:
            try:
                mtb = int(row[0])
                dbanswers.append((mtb, row[idx]))
            except ValueError as e:
                current_app.logger.error(f"Error parsing value: {e}")

    xml = create_measure_sheet(dataset=dbanswers)
    return render_template(
        "statistics/stats-messtischblatt.html",
        menu=list_of_stats,
        svg=xml,
        marker=marker,
    )


def stats_bardiagram_datum(dbfields, page, marker=None):
    """Calculate statistics by date using ORM queries."""

    date_from = date.fromisoformat(session["date_from"])
    date_to = date.fromisoformat(session["date_to"])

    results = {0: {}, 1: {}}
    for idx, field_name in enumerate(dbfields):
        col = getattr(TblMeldungen, field_name)
        stmt = (
            select(col.label("tag"), func.count(col).label("anzahl"))
            .join(TblMeldungen.fundort)
            .where(
                col.between(date_from, date_to),
                TblMeldungen.statuses.contains([ReportStatus.APPR.value]),
                TblFundorte.amt.like(f"{session['ags']}%"),
            )
            .group_by(col)
            .order_by(col)
        )
        rows = db.session.execute(stmt).all()

        trace = {"x": [], "y": []}
        for row in rows:
            trace["x"].append(str(row.tag))
            trace["y"].append(row.anzahl)
        results[idx] = trace

    return render_template(
        "statistics/" + page,
        menu=list_of_stats,
        trace1=results[0],
        trace2=results[1],
        marker=marker,
    )


def stats_geschlecht(marker):
    """Count sum of all kategories"""

    # Reuse shared aggregation columns, then relabel for German display
    _LABEL_MAP = {
        "maennlich": "Männchen",
        "weiblich": "Weibchen",
        "nymphe": "Nymphen",
        "oothek": "Ootheken",
        "andere": "Andere",
        "gesamt": "Gesamt",
    }

    stmt = (
        select(*_gender_sum_columns())
        .join(TblMeldungen.fundort)
        .where(
            TblMeldungen.dat_fund_von >= date.fromisoformat(session["date_from"]),
            TblMeldungen.dat_fund_von <= date.fromisoformat(session["date_to"]),
            TblFundorte.amt.like(f"{session['ags']}%"),
            TblMeldungen.statuses.contains([ReportStatus.APPR.value]),
        )
    )

    row = db.session.execute(stmt).first()
    res = {}
    if row:
        res = {_LABEL_MAP[k]: v for k, v in row._mapping.items()}

    return render_template(
        "statistics/stats-geschlecht.html",
        menu=list_of_stats,
        values=res,
        marker=marker,
    )


def stats_amt(marker):
    "Statistics pro Gemeinden (AGS))"

    totals = {
        "amt": "", "maennlich": 0, "weiblich": 0,
        "oothek": 0, "nymphe": 0, "andere": 0, "gesamt": 0,
    }
    fehler = False

    stmt = (
        select(TblFundorte.amt, *_gender_sum_columns())
        .join(TblMeldungen)
        .where(
            TblMeldungen.dat_meld >= date.fromisoformat(session["date_from"]),
            TblMeldungen.dat_meld <= date.fromisoformat(session["date_to"]),
            TblMeldungen.statuses.contains([ReportStatus.APPR.value]),
        )
        .where(TblFundorte.amt.like(f"{session['ags']}%"))
        .group_by(TblFundorte.amt)
    )
    results = db.session.execute(stmt).all()

    if results:
        gemeinde = results[0][0]
    else:
        gemeinde = ""
        fehler = True
    for row in results:
        totals["amt"] = row[0]
        totals["maennlich"] += row.maennlich or 0
        totals["weiblich"] += row.weiblich or 0
        totals["oothek"] += row.oothek or 0
        totals["nymphe"] += row.nymphe or 0
        totals["andere"] += row.andere or 0
        totals["gesamt"] += row.gesamt or 0

    # Convert to list format expected by template: [amt, m, w, o, n, a, g]
    dbanswers = [
        totals["amt"], totals["maennlich"], totals["weiblich"],
        totals["oothek"], totals["nymphe"], totals["andere"], totals["gesamt"],
    ]

    return render_template(
        "statistics/stats-gemeinde.html",
        menu=list_of_stats,
        result=dbanswers,
        gemeinde=gemeinde,
        fehler=fehler,
        marker=marker,
    )


def stats_laender(marker):
    "Statistics pro Bundesland (AGS))"

    substring_start = literal_column("1")
    state_code_len = literal_column("2")
    amt_group_expr = func.substring(TblFundorte.amt,
                                    substring_start,
                                    state_code_len)
    results = db.session.execute(
        select(amt_group_expr.label("amt_group"), *_gender_sum_columns())
        .join(TblMeldungen)
        .where(
            TblMeldungen.dat_meld >= date.fromisoformat(session["date_from"]),
            TblMeldungen.dat_meld <= date.fromisoformat(session["date_to"]),
            TblMeldungen.statuses.contains([ReportStatus.APPR.value]),
        )
        .group_by(amt_group_expr)
    ).all()

    result_dict = {}
    for row in results:
        if not row.amt_group:
            continue
        state_name = BUNDESLAENDER.get(row.amt_group, "Unbekannt")
        result_dict[f"{row.amt_group} --  {state_name}"] = {
            "maennlich": row.maennlich,
            "weiblich": row.weiblich,
            "oothek": row.oothek,
            "nymphe": row.nymphe,
            "andere": row.andere,
            "gesamt": row.gesamt,
        }

    return render_template(
        "statistics/stats-laender.html",
        menu=list_of_stats,
        result=result_dict,
        marker=marker,
    )


def stats_bundesland(marker):
    """
    Statistik für:
    - Brandenburg
    - Berlin nach Stadtbezirken (AGS))
    """

    if marker == "meldungen_berlin":
        ags = "11"
        maxchars = 8
        land = "Berlin"
        laender = BERLIN_BEZIRKE
    elif marker == "meldungen_brb":
        ags = "12"
        maxchars = 5
        land = "Brandenburg"
        laender = BRANDENBURG_LANDKREISE
    else:
        raise ValueError(f"Unsupported marker: {marker}")

    substring_start = literal_column("1")
    state_code_len = literal_column("2")
    district_len = literal_column(str(maxchars))
    state_prefix_expr = func.substring(
        TblFundorte.amt, substring_start, state_code_len
    )
    amt_group_expr = func.substring(TblFundorte.amt,
                                    substring_start,
                                    district_len)
    results = db.session.execute(
        select(amt_group_expr.label("amt_group"), *_gender_sum_columns())
        .join(TblMeldungen)
        .where(
            TblMeldungen.dat_meld >= date.fromisoformat(session["date_from"]),
            TblMeldungen.dat_meld <= date.fromisoformat(session["date_to"]),
            state_prefix_expr == ags,
            TblMeldungen.statuses.contains([ReportStatus.APPR.value]),
        )
        .group_by(amt_group_expr)
    ).all()

    result_dict = {}
    for row in results:
        if not row.amt_group:
            continue
        district_name = laender.get(row.amt_group, "Unbekannt")
        result_dict[f"{row.amt_group} -- {district_name}"] = {
            "maennlich": row.maennlich,
            "weiblich": row.weiblich,
            "oothek": row.oothek,
            "nymphe": row.nymphe,
            "andere": row.andere,
            "gesamt": row.gesamt,
        }

    return render_template(
        "statistics/stats-bundesland.html",
        menu=list_of_stats,
        result=result_dict,
        ags=ags,
        land=land,
        marker=marker,
    )


def stats_gesamt(marker):
    "Get sum for  Bundesland, Landkreis/Stadtbezirk and Amt"

    result_dict = build_gesamt_template()

    stmt = (
        select(
            TblFundorte.amt,
            func.sum(
                func.coalesce(TblMeldungen.art_m, 0)
                + func.coalesce(TblMeldungen.art_w, 0)
                + func.coalesce(TblMeldungen.art_o, 0)
                + func.coalesce(TblMeldungen.art_n, 0)
                + func.coalesce(TblMeldungen.art_f, 0)
            ).label("gesamt"),
        )
        .join(TblMeldungen)
        .where(
            TblMeldungen.dat_meld >= date.fromisoformat(session["date_from"]),
            TblMeldungen.dat_meld <= date.fromisoformat(session["date_to"]),
            TblMeldungen.statuses.contains([ReportStatus.APPR.value]),
        )
        .group_by(TblFundorte.amt)
    )

    results = db.session.execute(stmt).all()
    keys = set(result_dict.keys())
    for result in results:
        try:
            amt = result[0]
            if not amt:
                continue
            land_code = amt[:2]
            kreis_code = amt[:5]

            # Länder
            result_dict[land_code][3] += result[1]
            # Landkreise für Brandenburg
            if kreis_code in keys:
                result_dict[kreis_code][3] += result[1]
            # Berlin (full AMT code)
            if amt in keys:
                result_dict[amt][3] += result[1]
            # Berliner Stadtbezirke
            if amt.startswith("11"):
                result_dict["11"][4].append(
                    [amt, "", "", amt, result[1]]
                )
            # Brandenburg
            elif amt.startswith("12"):
                result_dict[kreis_code][4].append(
                    [amt, "", "", amt, result[1]]
                )
        except Exception as e:
            current_app.logger.error(
                f"Error in statistics query - Result: {result}, Error: {e}"
            )

    return render_template(
        "statistics/stats-table-all.html",
        menu=list_of_stats,
        result=result_dict,
        marker=marker,
    )


def stats_feedback(page, marker):
    """Summary of the feedback questions provided."""

    stmt = (
        select(
            TblUserFeedback.feedback_source,
            func.count(TblUserFeedback.id).label("cnt"),
        )
        .where(TblUserFeedback.feedback_source.is_not(None))
        .group_by(TblUserFeedback.feedback_source)
    )
    rows = db.session.execute(stmt).all()
    feedback = [
        (FeedbackSource.get_display_name(row.feedback_source), row.cnt)
        for row in rows
    ]

    stmt = (
        select(TblUserFeedback.source_detail)
        .where(TblUserFeedback.source_detail != "")
        .order_by(TblUserFeedback.id.desc())
        .limit(20)
    )
    rows = db.session.execute(stmt).all()
    details = [row.source_detail for row in rows]

    return render_template(
        "statistics/" + page,
        menu=list_of_stats,
        feedback=feedback,
        details=details,
        marker=marker,
    )
