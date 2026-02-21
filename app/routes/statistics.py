from flask import Blueprint
from flask import render_template, request, current_app
from flask import session
from sqlalchemy import func, text, select
from sqlalchemy import cast, String
from sqlalchemy import literal_column
from app import db
from app.database.models import TblAemterCoordinaten
from app.tools.check_reviewer import reviewer_required
from app.tools.gen_messtisch_svg import create_measure_sheet
from app.database.models import TblFundorte, TblMeldungen, ReportStatus
from datetime import date, datetime, timedelta
from collections import defaultdict
from app.database.feedback_type import FeedbackSource

stats = Blueprint("statistics", __name__)

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
    "feedback": "Feedback",
}


@stats.route("/statistik/ags", methods=["GET"])
def autocomplete_ags():
    q = request.args.get("ags_input", "").strip()
    if len(q) < 2:
        return ""
    dbsession = db.session
    try:
        stmt = (
            select(TblAemterCoordinaten.ags, TblAemterCoordinaten.gen)
            .where(
                (cast(TblAemterCoordinaten.ags, String).startswith(q))
                | (TblAemterCoordinaten.gen.ilike(f"{q}%"))
            )
            .order_by(TblAemterCoordinaten.gen)
            .limit(10)
        )

        rows = dbsession.execute(stmt).all()
        return "".join(
            f"""
            <li
                class="suggestion"
                data-ags="{ags}"
                data-gen="{gen}"
            >
                <strong>{ags}</strong>: {gen}
            </li>
            """
            for ags, gen in rows
        )

    finally:
        dbsession.close()


def get_date_interval():
    "Calculate and format start and end date"

    now = datetime.now().isoformat()
    last_year = datetime.now() - timedelta(weeks=52)
    last_year = last_year.isoformat()
    start_date = request.form.get("dateFrom", session.get("date_from", last_year))
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
                dbfields=["dat_meld"], page="stats-meldedatum.html", marker=value
            )
        case "meldungen_funddatum":
            return stats_bardiagram_datum(
                dbfields=["dat_fund_von"], page="stats-funddatum.html", marker=value
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


def stats_mtb(marker):
    "Results as MTB (Messtischblatt-Raster)"
    art = request.form.get("typeInput", "all")
    typeInput = ["mtb", "maennlich", "weiblich", "oothek", "nymphe", "andere", "all"]
    dbanswers = []
    stmt = (
        select(
            TblFundorte.mtb,
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
        )
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
    "Calculate statistics by date"

    results = {0: {}, 1: {}}
    for idx, dbfield in enumerate(dbfields):
        # Use parameterized query to prevent SQL injection
        # Array containment check: statuses @> '{APPR}' (APPR excludes DEL by design)
        stm = f"""
           SELECT {dbfield} as Tag,
           count({dbfield}) as Anzahl
           FROM (select {dbfield}
                from meldungen
                where {dbfield} BETWEEN CAST(:date_from AS date)
                                AND CAST(:date_to AS date)
                and statuses @> '{{APPR}}') as filtered
           GROUP BY filtered.{dbfield}
           ORDER by Tag;
        """
        sql = text(stm)
        result = db.session.execute(
            sql, {"date_from": session["date_from"], "date_to": session["date_to"]}
        )

        trace = {"x": [], "y": []}

        if result:
            for record in result:
                trace["x"].append(str(record[0]))
                trace["y"].append(record[1])
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

    stmt = (
        select(
            func.sum(func.coalesce(TblMeldungen.art_m, 0)).label("Männchen"),
            func.sum(func.coalesce(TblMeldungen.art_w, 0)).label("Weibchen"),
            func.sum(func.coalesce(TblMeldungen.art_n, 0)).label("Nymphen"),
            func.sum(func.coalesce(TblMeldungen.art_o, 0)).label("Ootheken"),
            func.sum(func.coalesce(TblMeldungen.art_f, 0)).label("Andere"),
            func.sum(
                func.coalesce(TblMeldungen.art_m, 0)
                + func.coalesce(TblMeldungen.art_w, 0)
                + func.coalesce(TblMeldungen.art_n, 0)
                + func.coalesce(TblMeldungen.art_o, 0)
                + func.coalesce(TblMeldungen.art_f, 0)
            ).label("Gesamt"),
        )
        .join(TblMeldungen.fundort)
        .where(
            TblMeldungen.dat_fund_von >= date.fromisoformat(session["date_from"]),
            TblMeldungen.dat_fund_von <= date.fromisoformat(session["date_to"]),
            TblFundorte.amt.like(f"{session['ags']}%"),
            TblMeldungen.statuses.contains([ReportStatus.APPR.value]),
        )
    )

    result = db.session.execute(stmt).all()
    res = []
    for row in result:
        row = row._mapping
        res = dict((name, val) for name, val in row.items())

    return render_template(
        "statistics/stats-geschlecht.html",
        menu=list_of_stats,
        values=res,
        marker=marker,
    )


def stats_amt(marker):
    "Statistics pro Gemeinden (AGS))"

    typeInput = ["amt", "maennlich", "weiblich", "oothek", "nymphe", "andere", "all"]
    dbanswers = ["", 0, 0, 0, 0, 0, 0]
    fehler = False

    stmt = (
        select(
            TblFundorte.amt,
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
        )
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
        dbanswers[0] = row[0]
        for idx, val in enumerate(typeInput):
            if idx > 0:
                try:
                    dbanswers[idx] += row[idx]
                except ValueError as e:
                    current_app.logger.error(f"Error parsing value: {e}")

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
    amt_group_expr = func.substring(TblFundorte.amt, substring_start, state_code_len)

    stmt = (
        select(
            amt_group_expr.label("amt_group"),
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
        )
        .join(TblMeldungen)
        .where(
            TblMeldungen.dat_meld >= date.fromisoformat(session["date_from"]),
            TblMeldungen.dat_meld <= date.fromisoformat(session["date_to"]),
            TblMeldungen.statuses.contains([ReportStatus.APPR.value]),
        )
        .group_by(amt_group_expr)
    )

    results = db.session.execute(stmt).all()

    laender = {
        "01": "Schleswig-Holstein",
        "02": "Freie und Hansestadt Hamburg",
        "03": "Niedersachsen",
        "04": "Freie Hansestadt Bremen",
        "05": "Nordrhein-Westfalen",
        "06": "Hessen",
        "07": "Rheinland-Pfalz",
        "08": "Baden-Württemberg",
        "09": "Freistaat Bayern",
        "10": "Saarland⁠",
        "11": "Berlin⁠",
        "12": "Brandenburg",
        "13": "Mecklenburg-Vorpommern",
        "14": "Freistaat Sachsen",
        "15": "Sachsen-Anhalt",
        "16": "Freistaat Thüringen",
    }

    result_dict = defaultdict(dict)
    for result in results:
        if result.amt_group:
            state_name = laender.get(result.amt_group, "Unbekannt")
            result_dict[f"{result.amt_group} --  {state_name}"] = {
                "maennlich": result.maennlich,
                "weiblich": result.weiblich,
                "oothek": result.oothek,
                "nymphe": result.nymphe,
                "andere": result.andere,
                "gesamt": result.gesamt,
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
        laender = {
            "11000000": "Berlin (allgemein)",
            "11000001": "Mitte",
            "11000002": "Friedrichshain-Kreuzberg",
            "11000003": "Pankow",
            "11000004": "Charlottenburg-Wilmersdorf",
            "11000005": "Spandau",
            "11000006": "Steglitz-Zehlendorf",
            "11000007": "Tempelhof-Schöneberg",
            "11000008": "Neukölln",
            "11000009": "Treptow-Köpenick",
            "11000010": "Marzahn-Hellersdorf",
            "11000011": "Lichtenberg",
            "11000012": "Reinickendorf",
        }
    elif marker == "meldungen_brb":
        ags = "12"
        maxchars = 5
        land = "Brandenburg"
        laender = {
            "12060": "Landkreis Barnim",
            "12061": "Landkreis Dahme-Spreewald",
            "12062": "Landkreis Elbe-Elster",
            "12063": "Landkreis Havelland",
            "12064": "Landkreis Märkisch-Oderland",
            "12065": "Landkreis Oberhavel",
            "12066": "Landkreis Oberspreewald-Lausitz",
            "12067": "Landkreis Oder-Spree",
            "12068": "Landkreis Ostprignitz-Ruppin",
            "12069": "Landkreis Potsdam-Mittelmark",
            "12070": "Landkreis Prignitz",
            "12071": "Landkreis Spree-Neiße",
            "12072": "Landkreis Teltow-Fläming",
            "12073": "Landkreis Uckermark",
            "12051": "Brandenburg an der Havel",
            "12052": "Cottbus",
            "12053": "Frankfurt (Oder)",
            "12054": "Potsdam",
        }

    substring_start = literal_column("1")
    state_code_len = literal_column("2")
    district_len = literal_column(str(maxchars))
    state_prefix_expr = func.substring(
        TblFundorte.amt, substring_start, state_code_len
    )
    amt_group_expr = func.substring(TblFundorte.amt, substring_start, district_len)

    stmt = (
        select(
            amt_group_expr.label("amt_group"),
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
        )
        .join(TblMeldungen)
        .where(
            TblMeldungen.dat_meld >= date.fromisoformat(session["date_from"]),
            TblMeldungen.dat_meld <= date.fromisoformat(session["date_to"]),
            state_prefix_expr == ags,
            TblMeldungen.statuses.contains([ReportStatus.APPR.value]),
        )
        .group_by(amt_group_expr)
    )

    results = db.session.execute(stmt).all()

    result_dict = defaultdict(dict)
    for result in results:
        if result.amt_group:
            district_name = laender.get(result.amt_group, "Unbekannt")
            result_dict[f"{result.amt_group} -- {district_name}"] = {
                "maennlich": result.maennlich,
                "weiblich": result.weiblich,
                "oothek": result.oothek,
                "nymphe": result.nymphe,
                "andere": result.andere,
                "gesamt": result.gesamt,
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

    result_dict = {
        "12": ["Brandenburg", "", "", 0, []],
        "12060": ["", "Landkreis Barnim", "", 0, []],
        "12061": ["", "Landkreis Dahme-Spreewald", "", 0, []],
        "12062": ["", "Landkreis Elbe-Elster", "", 0, []],
        "12063": ["", "Landkreis Havelland", "", 0, []],
        "12064": ["", "Landkreis Märkisch-Oderland", "", 0, []],
        "12065": ["", "Landkreis Oberhavel", "", 0, []],
        "12066": ["", "Landkreis Oberspreewald-Lausitz", "", 0, []],
        "12067": ["", "Landkreis Oder-Spree", "", 0, []],
        "12068": ["", "Landkreis Ostprignitz-Ruppin", "", 0, []],
        "12069": ["", "Landkreis Potsdam-Mittelmark", "", 0, []],
        "12070": ["", "Landkreis Prignitz", "", 0, []],
        "12071": ["", "Landkreis Spree-Neiße", "", 0, []],
        "12072": ["", "Landkreis Teltow-Fläming", "", 0, []],
        "12073": ["", "Landkreis Uckermark", "", 0, []],
        "12051": ["", "Brandenburg an der Havel", "", 0, []],
        "12052": ["", "Cottbus", "", 0, []],
        "12053": ["", "Frankfurt (Oder)", "", 0, []],
        "12054": ["", "Potsdam", "", 0, []],
        "11": ["Berlin⁠", "", "", 0, []],
        "13": ["Mecklenburg-Vorpommern", "", "", 0, []],
        "14": ["Freistaat Sachsen", "", "", 0, []],
        "15": ["Sachsen-Anhalt", "", "", 0, []],
        "16": ["Freistaat Thüringen", "", "", 0, []],
        "01": ["Schleswig-Holstein", "", "", 0, []],
        "02": ["Freie und Hansestadt Hamburg", "", "", 0, []],
        "03": ["Niedersachsen", "", "", 0, []],
        "04": ["Freie Hansestadt Bremen", "", "", 0, []],
        "05": ["Nordrhein-Westfalen", "", "", 0, []],
        "06": ["Hessen", "", "", 0, []],
        "07": ["Rheinland-Pfalz", "", "", 0, []],
        "08": ["Baden-Württemberg", "", "", 0, []],
        "09": ["Freistaat Bayern", "", "", 0, []],
        "10": ["Saarland⁠", "", "", 0, []],
    }

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
    keys = list(result_dict.keys())
    for result in results:
        try:
            if result[0]:
                # Länder
                result_dict[f"{result[0][:2]}"][3] += result[1]
                # Landkreise für Brandenburg
                if str(f"{result[0][:5]}") in keys:
                    result_dict[f"{result[0][:5]}"][3] += result[1]
                # Berlin
                if str(f"{result[0]}") in keys:
                    result_dict[f"{result[0]}"][3] += result[1]
                # Berliner Stadtbezirke
                if result[0].startswith("11"):
                    id, gemeinde = result[0][:2]
                    result_dict["11"][4].append(
                        [result[0], "", "", gemeinde, result[1]]
                    )

                # Brandenburg
                if result[0].startswith("12"):
                    id, gemeinde = result[0][:2]
                    result_dict[f"{result[0][:5]}"][4].append(
                        [result[0], "", "", gemeinde, result[1]]
                    )
        except Exception as e:
            current_app.logger.error(f"""
            Error in statistics query - Result: {result}, Error: {e}
            """)

    return render_template(
        "statistics/stats-table-all.html",
        menu=list_of_stats,
        result=result_dict,
        marker=marker,
    )


def stats_feedback(page, marker):
    "Summary of the feedback questions provided"

    stm = """
    SELECT feedback_source, count(*)
    FROM user_feedback
    WHERE feedback_source IS NOT NULL
    GROUP BY feedback_source;
    """
    sql = text(stm)
    result = db.session.execute(sql)

    feedback = []

    if result:
        for record in result:
            feedback.append((FeedbackSource.get_display_name(record[0]), record[1]))

    stm = """
    SELECT source_detail
    FROM user_feedback
    where source_detail <> ''
    ORDER BY id desc Limit 20;
    """
    sql = text(stm)
    result = db.session.execute(sql)

    details = []
    if result:
        for record in result:
            details.append(record[0])

    return render_template(
        "statistics/" + page,
        menu=list_of_stats,
        feedback=feedback,
        details=details,
        marker=marker,
    )
