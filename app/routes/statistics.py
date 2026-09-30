from datetime import date, timedelta
from functools import partial

from flask import Blueprint, current_app, render_template, request, session, url_for
from sqlalchemy import String, cast, func, literal_column, select

from app.auth import reviewer_required
from app.database.ags import (
    BERLIN_BEZIRKE,
    BRANDENBURG_LANDKREISE,
    BUNDESLAENDER,
    build_gesamt_template,
)
from app.database.feedback_type import FeedbackSource
from app.database.models import (
    TblAemterCoordinaten,
    TblFundorte,
    TblMeldungen,
    TblMeldungUser,
    TblUserFeedback,
    TblUsers,
)
from app.extensions import db
from app.tools.gen_messtisch_svg import create_measure_sheet

stats = Blueprint("statistics", __name__)


def _total_animals():
    """Use the recorded animal count, with classified counts for legacy NULLs."""
    return func.sum(
        func.coalesce(
            TblMeldungen.tiere,
            func.coalesce(TblMeldungen.art_m, 0)
            + func.coalesce(TblMeldungen.art_w, 0)
            + func.coalesce(TblMeldungen.art_o, 0)
            + func.coalesce(TblMeldungen.art_n, 0)
            + func.coalesce(TblMeldungen.art_f, 0),
        )
    ).label("gesamt")


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
        _total_animals(),
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
    "observer": "Fleißige Melder",
}


@stats.context_processor
def _menu_context():
    return {"menu": list_of_stats, "marker": session.get("marker")}


COUNT_KEYS = ("maennlich", "weiblich", "oothek", "nymphe", "andere", "gesamt")


def _filters():
    """Return date_from, date_to and the AGS prefix stored by stats_start."""
    return (
        date.fromisoformat(session["date_from"]),
        date.fromisoformat(session["date_to"]),
        session["ags"],
    )


def _counts_by_group(rows, names, separator):
    """Map "<code><separator><name>" to the gender/stage counts of each row."""
    return {
        f"{row.amt_group}{separator}{names.get(row.amt_group, 'Unbekannt')}": {
            key: getattr(row, key) for key in COUNT_KEYS
        }
        for row in rows
        if row.amt_group
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
    return render_template("statistics/partials/_ags_options.html", rows=rows)


def _iso_date_or(value, fallback):
    """Return an ISO date string, falling back on anything unparsable.

    The result is stored in the session and read back by every statistics view,
    so a value date.fromisoformat cannot read is not one bad response — it
    raises again on every later request from that browser until the cookie is
    replaced.
    """
    try:
        return date.fromisoformat(str(value)[:10]).isoformat()
    except (TypeError, ValueError):
        return fallback


def get_date_interval():
    "Calculate and format start and end date"

    today = date.today()

    return (
        _iso_date_or(
            request.form.get("dateFrom", session.get("date_from")),
            (today - timedelta(weeks=52)).isoformat(),
        ),
        _iso_date_or(
            request.form.get("dateTo", session.get("date_to")),
            today.isoformat(),
        ),
    )


@stats.route("/statistik", methods=["POST", "GET"])
@reviewer_required
def stats_start():
    "Startseite für alle Statistiken"

    session["date_from"], session["date_to"] = get_date_interval()
    session["ags"] = request.form.get("ags", session.get("ags", "")).strip()

    value = request.form.get("stats", "start")
    session["marker"] = value

    view = STATS_VIEWS.get(value)
    if view is None:
        return render_template("statistics/statistiken.html")
    return view()


def stats_daily_average():
    """Get reports based on hours

    We are using timestamps included in image names
    (column »ablage« in table fundorte).
    """

    timestamp_substr = func.substring(TblFundorte.ablage, r"-([0-9]{14})-")
    timestamp_expr = func.to_timestamp(timestamp_substr, "YYYYMMDDHH24MISS")
    hour_expr = func.extract("hour", timestamp_expr)

    date_from, date_to, ags = _filters()

    stmt = (
        select(hour_expr.label("stunde"), func.count().label("anzahl_meldungen"))
        .join(TblMeldungen)
        .where(
            timestamp_substr.isnot(None),
            TblMeldungen.dat_fund_von >= date_from,
            TblMeldungen.dat_fund_von <= date_to,
            TblMeldungen.is_approved,
        )
        .where(TblFundorte.amt.like(f"{ags}%"))
        .group_by(hour_expr)
        .order_by(hour_expr)
    )

    results = db.session.execute(stmt).all()

    daily = {str(hour): 0 for hour in range(24)}

    for row in results:
        daily[str(int(row[0]))] = row[1]

    return render_template("statistics/stats-daily-average.html", daten=daily)


# typeInput value -> the _gender_sum_columns label it counts
MTB_COUNTS = {
    "maennlich": "maennlich",
    "weiblich": "weiblich",
    "oothek": "oothek",
    "nymphe": "nymphe",
    "andere": "andere",
    "all": "gesamt",
}


def stats_mtb():
    "Results as MTB (Messtischblatt-Raster)"

    column = MTB_COUNTS.get(request.form.get("typeInput", "all"), "gesamt")
    date_from, date_to, ags = _filters()
    stmt = (
        select(TblFundorte.mtb, *_gender_sum_columns())
        .join(TblMeldungen)
        .where(
            TblMeldungen.dat_fund_von >= date_from,
            TblMeldungen.dat_fund_von <= date_to,
            TblMeldungen.is_approved,
            # Fundorte outside Germany have no sheet.
            TblFundorte.mtb != "",
        )
        .where(TblFundorte.amt.like(f"{ags}%"))
        .group_by(TblFundorte.mtb)
    )

    dbanswers = []
    for row in db.session.execute(stmt):
        count = row._mapping[column]
        if count > 0:
            try:
                dbanswers.append((int(row.mtb), count))
            except ValueError:
                current_app.logger.warning("Unreadable Messtischblatt %r", row.mtb)

    bg_url = url_for("static", filename="images/land_brandenburg.svg")
    xml = create_measure_sheet(dataset=dbanswers, bg_image_url=bg_url)
    return render_template("statistics/stats-messtischblatt.html", svg=xml)


def stats_bardiagram_datum(dbfields, page):
    """Calculate statistics by date using ORM queries."""

    date_from, date_to, ags = _filters()

    results = {0: {}, 1: {}}
    for idx, field_name in enumerate(dbfields):
        col = getattr(TblMeldungen, field_name)
        stmt = (
            select(col.label("tag"), func.count(col).label("anzahl"))
            .join(TblMeldungen.fundort)
            .where(
                col.between(date_from, date_to),
                TblMeldungen.is_approved,
                TblFundorte.amt.like(f"{ags}%"),
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

    return render_template("statistics/" + page, trace1=results[0], trace2=results[1])


def stats_geschlecht():
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

    date_from, date_to, ags = _filters()
    stmt = (
        select(*_gender_sum_columns())
        .join(TblMeldungen.fundort)
        .where(
            TblMeldungen.dat_fund_von >= date_from,
            TblMeldungen.dat_fund_von <= date_to,
            TblFundorte.amt.like(f"{ags}%"),
            TblMeldungen.is_approved,
        )
    )

    row = db.session.execute(stmt).first()
    res = {}
    if row:
        res = {_LABEL_MAP[k]: v for k, v in row._mapping.items()}

    return render_template("statistics/stats-geschlecht.html", values=res)


def stats_amt():
    "Statistics pro Gemeinden (AGS))"

    date_from, date_to, ags = _filters()
    stmt = (
        select(TblFundorte.amt, *_gender_sum_columns())
        .join(TblMeldungen)
        .where(
            TblMeldungen.dat_meld >= date_from,
            TblMeldungen.dat_meld <= date_to,
            TblMeldungen.is_approved,
        )
        .where(TblFundorte.amt.like(f"{ags}%"))
        .group_by(TblFundorte.amt)
    )
    results = db.session.execute(stmt).all()

    # Template row: [amt, m, w, o, n, a, g]; the amt is the last group's.
    dbanswers = [
        results[-1].amt if results else "",
        *(sum(getattr(row, key) or 0 for row in results) for key in COUNT_KEYS),
    ]

    return render_template(
        "statistics/stats-gemeinde.html",
        result=dbanswers,
        gemeinde=results[0].amt if results else "",
        fehler=not results,
    )


def stats_laender():
    "Statistics pro Bundesland (AGS))"

    substring_start = literal_column("1")
    state_code_len = literal_column("2")
    amt_group_expr = func.substring(TblFundorte.amt, substring_start, state_code_len)
    date_from, date_to, _ = _filters()
    results = db.session.execute(
        select(amt_group_expr.label("amt_group"), *_gender_sum_columns())
        .join(TblMeldungen)
        .where(
            TblMeldungen.dat_meld >= date_from,
            TblMeldungen.dat_meld <= date_to,
            TblMeldungen.is_approved,
        )
        .group_by(amt_group_expr)
    ).all()

    return render_template(
        "statistics/stats-laender.html",
        result=_counts_by_group(results, BUNDESLAENDER, " --  "),
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
    state_prefix_expr = func.substring(TblFundorte.amt, substring_start, state_code_len)
    amt_group_expr = func.substring(TblFundorte.amt, substring_start, district_len)
    date_from, date_to, _ = _filters()
    results = db.session.execute(
        select(amt_group_expr.label("amt_group"), *_gender_sum_columns())
        .join(TblMeldungen)
        .where(
            TblMeldungen.dat_meld >= date_from,
            TblMeldungen.dat_meld <= date_to,
            state_prefix_expr == ags,
            TblMeldungen.is_approved,
        )
        .group_by(amt_group_expr)
    ).all()

    return render_template(
        "statistics/stats-bundesland.html",
        result=_counts_by_group(results, laender, " -- "),
        ags=ags,
        land=land,
    )


def stats_gesamt():
    "Get sum for  Bundesland, Landkreis/Stadtbezirk and Amt"

    result_dict = build_gesamt_template()

    date_from, date_to, _ = _filters()
    stmt = (
        select(TblFundorte.amt, _total_animals())
        .join(TblMeldungen)
        .where(
            TblMeldungen.dat_meld >= date_from,
            TblMeldungen.dat_meld <= date_to,
            TblMeldungen.is_approved,
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
                result_dict["11"][4].append([amt, "", "", amt, result[1]])
            # Brandenburg
            elif amt.startswith("12"):
                result_dict[kreis_code][4].append([amt, "", "", amt, result[1]])
        except KeyError:
            current_app.logger.exception(
                "Error in statistics query - Result: %s", result
            )

    return render_template("statistics/stats-table-all.html", result=result_dict)


def stats_feedback():
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
        (FeedbackSource.get_display_name(row.feedback_source), row.cnt) for row in rows
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
        "statistics/stats-feedback.html", feedback=feedback, details=details
    )


def stats_observer():
    """Reporters by number of reports, most first."""
    count = func.count(TblMeldungUser.id).label("anzahl")
    stmt = (
        select(count, TblUsers.user_name, TblUsers.user_kontakt)
        .join(TblUsers, TblUsers.id == TblMeldungUser.id_user)
        .where(TblUsers.user_kontakt.is_not(None))
        .group_by(TblUsers.user_kontakt, TblUsers.user_name)
        .order_by(count.desc())
    )
    observers = db.session.execute(stmt).all()
    return render_template("statistics/stats-observer.html", observers=observers)


STATS_VIEWS = {
    "geschlecht": stats_geschlecht,
    "meldungen_meldedatum": partial(
        stats_bardiagram_datum, ["dat_meld"], "stats-meldedatum.html"
    ),
    "meldungen_funddatum": partial(
        stats_bardiagram_datum, ["dat_fund_von"], "stats-funddatum.html"
    ),
    "meldungen_meld_fund": partial(
        stats_bardiagram_datum, ["dat_fund_von", "dat_meld"], "stats-meld-fund.html"
    ),
    "meldungen_mtb": stats_mtb,
    "meldungen_amt": stats_amt,
    "meldungen_laender": stats_laender,
    "meldungen_brb": partial(stats_bundesland, "meldungen_brb"),
    "meldungen_berlin": partial(stats_bundesland, "meldungen_berlin"),
    "meldungen_gesamt": stats_gesamt,
    "meldungen_zeiten": stats_daily_average,
    "feedback": stats_feedback,
    "observer": stats_observer,
}
