from flask import Blueprint
from flask import render_template, request
from flask import session, abort
from sqlalchemy import func, text
from app import db
from app.database.models import TblUsers
from app.tools.check_reviewer import login_required
from app.tools.gen_messtisch_svg import create_measure_sheet
from app.database.models import TblFundorte, TblMeldungen
from datetime import datetime, timedelta

stats = Blueprint("statistics", __name__)

list_of_stats = {
    "xxx": "Bitte eine Wahl treffen ...",
    "start": "Statistik: Startseite",
    "geschlecht": "Entwicklungsstadium/Geschlecht",
    "meldungen_funddatum": "Meldungen: Funddatum",
    "meldungen_meldedatum": "Meldungen: Meldedatum",
    "meldungen_meld_fund": "Meldungen: Fund- und Meldedatum",
    "meldungen_mtb": "Grafik: Messtischblatt",
}


def get_date_interval(request=None):
    "Calculate and format start and end date"

    start_date = None
    end_date = None
    now = datetime.now().isoformat()
    last_year = datetime.now() - timedelta(weeks=52)
    last_year = last_year.isoformat()
    if request:
        start_date = request.form.get("dateFrom", last_year)
        end_date = request.form.get("dateTo", now)
    if not end_date:
        end_date = now
    if not start_date:
        start_date = last_year

    return (start_date[:10], end_date[:10])


@stats.route("/statistik", methods=["POST", "GET"])
@stats.route("/statistik/<usrid>", methods=["POST", "GET"])
@login_required
def stats_start(usrid=None):
    "Startseite für alle Statistiken"

    user_id = session["user_id"]
    user = TblUsers.query.filter_by(user_id=user_id).first()

    # If the user doesn't exist or the role isn't 9, return 404
    if not user or user.user_rolle != "9":
        abort(403)
    """[
    ('statusInput', 'all'),
    ('typeInput', 'all'),
    ('dateFrom', ''),
    ('dateTo', ''),
    ('userId', '9999'),
    ('stats', 'geschlecht')]
    """
    start_date, end_date = get_date_interval(request)
    value = request.form.get("stats", "start")

    if value == "geschlecht":
        return stats_geschlecht(request)
    elif value == "meldungen_meldedatum":
        return stats_bardiagram_datum(
            request,
            dbfields=['dat_meld'],
            page='stats-meldedatum.html',
            marker="meldungen_meldedatum",
            dateFrom=start_date,
            dateTo=end_date)
    elif value == "meldungen_funddatum":
        return stats_bardiagram_datum(
            request,
            dbfields=['dat_fund_von'],
            page='stats-funddatum.html',
            marker="meldungen_funddatum",
            dateFrom=start_date,
            dateTo=end_date)
    elif value == "meldungen_meld_fund":
        return stats_bardiagram_datum(
            request,
            dbfields=['dat_fund_von', 'dat_meld'],
            page='stats-meld-fund.html',
            marker="meldungen_meld_fund",
            dateFrom=start_date,
            dateTo=end_date)
    elif value == "meldungen_mtb":
        return stats_mtb(request,
                         dateFrom=start_date,
                         dateTo=end_date,
                         marker="meldungen_mtb")
    elif value == "start":
        start_date, end_date = get_date_interval()

        return render_template(
            "statistics/statistiken.html",
            user_id=session["user_id"],
            menu=list_of_stats,
            marker="start",
            dateFrom=start_date,
            dateTo=end_date
        )
    else:
        return render_template(
            "statistics/statistiken.html",
            user_id=session["user_id"],
            menu=list_of_stats,
            marker="start",
            dateFrom=start_date,
            dateTo=end_date
        )


def stats_mtb(request, dateFrom, dateTo, marker):
    "Results as MTB (Messtischblatt-Raster)"

    art = request.form.get('typeInput', 'all')
    typeInput = ['mtb', 'maennlich', 'weiblich', 'oothek',
                 'nymphe', 'andere', 'all']
    conn = db.session
    dbanswers = []
    query = conn.query(
        TblFundorte.mtb,
        func.sum(func.COALESCE(TblMeldungen.art_m, 0)).label('maennlich'),
        func.sum(func.COALESCE(TblMeldungen.art_w, 0)).label('weiblich'),
        func.sum(func.COALESCE(TblMeldungen.art_o, 0)).label('oothek'),
        func.sum(func.COALESCE(TblMeldungen.art_n, 0)).label('nymphe'),
        func.sum(func.COALESCE(TblMeldungen.art_f, 0)).label('andere'),
        func.sum(func.COALESCE(TblMeldungen.art_m, 0) +
                 func.COALESCE(TblMeldungen.art_w, 0) +
                 func.COALESCE(TblMeldungen.art_o, 0) +
                 func.COALESCE(TblMeldungen.art_n, 0) +
                 func.COALESCE(TblMeldungen.art_f, 0)).label('gesamt')
    ).join(TblMeldungen).filter(
        func.age(TblMeldungen.dat_meld, dateFrom) >= '0 days',
        func.age(TblMeldungen.dat_meld, dateTo) < '1 day'
    ).group_by(
        TblFundorte.mtb
    )
    results = query.all()

    idx = typeInput.index(art)

    for row in results[1:]:
        if row[idx] > 0 and row[0] is not None:
            try:
                mtb = int(row[0])
                dbanswers.append((mtb, row[idx]))
            except ValueError as e:
                print(e)

    xml = create_measure_sheet(dataset=dbanswers)
    return render_template(
        "statistics/stats-messtischblatt.html",
        user_id=session["user_id"],
        menu=list_of_stats,
        marker=marker,
        svg=xml,
        dateFrom=dateFrom,
        dateTo=dateTo
    )


def stats_bardiagram_datum(request, dbfields,
                           page, marker,
                           dateFrom, dateTo):
    "Calculate statistics by date"
    results = {0: '', 1: ''}
    for idx, dbfield in enumerate(dbfields):
        stm = f"""
           SELECT {dbfield} as Tag,
           count({dbfield}) as Anzahl
           FROM (select {dbfield}
                from meldungen
                where {dbfield} BETWEEN '{dateFrom}'::date
                                AND ('{dateTo}'::date)
                and (deleted IS NULL or deleted != 'f')) as filtered
           GROUP BY filtered.{dbfield}
           ORDER by Tag;
        """
        sql = text(stm)
        with db.engine.connect() as conn:
            result = conn.execute(sql)

        trace = {"x": [], "y": []}

        if result:
            for record in result:
                trace["x"].append(str(record[0]))
                trace["y"].append(record[1])
        results[idx] = trace

    return render_template(
        "statistics/" + page,
        menu=list_of_stats,
        marker=marker,
        user_id=session["user_id"],
        trace1=results[0],
        trace2=results[1],
        dateFrom=dateFrom,
        dateTo=dateTo
    )


def stats_geschlecht(request=None):
    """Count sum of all kategories"""

    start_date, end_date = get_date_interval(request)
    stm = f"""
      select sum(art_m) as "Männchen"
            , sum(art_w) as "Weibchen"
            , sum(art_n) as "Nymphen"
            , sum(art_o) as "Ootheken"
            , sum(art_f) as "Andere"
      from (select art_m, art_w, art_n, art_o, art_f
            from meldungen
            where dat_fund_von >= to_date('{start_date}', 'YYYY-MM-DD')
            and dat_fund_von <= to_date('{end_date}', 'YYYY-MM-DD')
            and deleted is NULL or 'f') as filtered;"""

    sql = text(stm)

    with db.engine.connect() as conn:
        result = conn.execute(sql)
        res = []
        for row in result:
            row = row._mapping
            res = dict((name, val) for name, val in row.items())

    return render_template(
        "statistics/stats-geschlecht.html",
        menu=list_of_stats,
        user_id=session["user_id"],
        marker="geschlecht",
        dateFrom=start_date,
        dateTo=end_date,
        values=res,
    )
