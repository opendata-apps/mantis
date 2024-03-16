import json
from flask import Blueprint
from flask import render_template, request
from flask import session, abort
from sqlalchemy import func
from app import db
from app.database.models import TblUsers
from app.tools.check_reviewer import login_required
from app.tools.gen_messtisch_svg import create_measure_sheet
from app.database.models import TblFundorte

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


@stats.route("/statistik", methods=["POST"])
@stats.route("/statistik/<usrid>", methods=["GET"])
@login_required
def stats_start(usrid=None):
    "Startseite für alle Statistiken"
    user_id = session["user_id"]
    user = TblUsers.query.filter_by(user_id=user_id).first()

    # If the user doesn't exist or the role isn't 9, return 404
    if not user or user.user_rolle != "9":
        abort(403)

    value = request.form.get("stats", "start")
    if value == "geschlecht":
        return stats_geschlecht()
    elif value == "meldungen_meldedatum":
        return stats_meldungen_meldedatum()
    elif value == "meldungen_funddatum":
        return stats_meldungen_funddatum()
    elif value == "meldungen_meld_fund":
        return stats_meldungen_meld_fund()
    elif value == "meldungen_mtb":
        return stats_mtb()
    elif value == "start":
        return render_template(
            "statistics/statistiken.html",
            user_id=session["user_id"],
            menu=list_of_stats,
            marker="start",
        )
    else:
        return render_template(
            "statistics/statistiken.html",
            user_id=session["user_id"],
            menu=list_of_stats,
            marker="start",
        )


def stats_mtb(request=None):
    "Messtischblattauswertung für eine Grafik"

    dbanswers=[]
    stmt = "select mtb, count(mtb) from fundorte group by mtb;"
    res = db.session.query(
        TblFundorte.mtb,
        func.count(TblFundorte.mtb)).group_by(TblFundorte.mtb).all()
        
    for row in res:
        try:
            mtb = int(row[0])
            dbanswers.append((mtb, row[1]))
        except:
            pass
    xml = create_measure_sheet(dataset=dbanswers)
    return render_template(
        "statistics/stats-messtischblatt.html",
        user_id=session["user_id"],
        menu=list_of_stats,
        marker="start",
        svg=xml
    )

    

def stats_geschlecht(request=None):
    "Count sum of all kategories"

    sql = text(
        """
      select sum(art_m) as "Männchen"
            , sum(art_w) as "Weibchen"
            , sum(art_n) as "Nymphen"
            , sum(art_o) as "Ootheken"
            , sum(art_f) as "Andere"
      from meldungen
      where deleted is NULL;
    """
    )

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
        values=res,
    )


def stats_meldungen_meldedatum(request=None):
    "Cluster messages per dat_meld"

    sql = text(
        """ SELECT dat_meld as Tag,
                   count(dat_meld) as Anzahl
                   FROM meldungen
                   GROUP BY Tag
                   ORDER by Tag;"""
    )
    with db.engine.connect() as conn:
        result = conn.execute(sql)

    trace1 = {"x": [], "y": []}

    if result:
        for record in result:
            trace1["x"].append(str(record[0]))
            trace1["y"].append(record[1])
        else:
            pass
    res = json.loads(json.dumps(trace1))

    return render_template(
        "statistics/stats-meldedatum.html",
        menu=list_of_stats,
        marker="medlungen_meldedatum",
        user_id=session["user_id"],
        values=res,
    )


def stats_meldungen_funddatum(request=None):
    "Cluster messages per dat_fund"

    sql = text(
        """ SELECT dat_fund_von as Tag,
                   count(dat_fund_von) as Anzahl
                   FROM meldungen
                   GROUP BY Tag
                   ORDER by Tag;"""
    )
    with db.engine.connect() as conn:
        result = conn.execute(sql)

    trace1 = {"x": [], "y": []}

    if result:
        for record in result:
            trace1["x"].append(str(record[0]))
            trace1["y"].append(record[1])
        else:
            pass
    res = json.loads(json.dumps(trace1))

    return render_template(
        "statistics/stats-funddatum.html",
        menu=list_of_stats,
        marker="meldungen_funddatum",
        user_id=session["user_id"],
        values=res,
    )


def stats_meldungen_meld_fund(request=None):
    "Cluster messages per day"

    #    dbsession = db.engine.connect()
    sql = text(
        """ SELECT dat_meld as Tag,
                   count(dat_meld) as Anzahl
                   FROM meldungen
                   GROUP BY Tag
                   ORDER by Tag;"""
    )
    with db.engine.connect() as conn:
        result = conn.execute(sql)

    trace1 = {"x": [], "y": []}

    if result:
        for record in result:
            trace1["x"].append(str(record[0]))
            trace1["y"].append(record[1])
        else:
            pass
    res_trace1 = json.loads(json.dumps(trace1))

    sql = text(
        """ SELECT dat_fund_von as Tag,
                   count(dat_fund_von) as Anzahl
                   FROM meldungen
                   GROUP BY Tag
                   ORDER by Tag;"""
    )
    with db.engine.connect() as conn:
        result = conn.execute(sql)

    trace2 = {"x": [], "y": []}

    if result:
        for record in result:
            trace2["x"].append(str(record[0]))
            trace2["y"].append(record[1])
        else:
            pass
    res_trace2 = json.loads(json.dumps(trace2))
    return render_template(
        "statistics/stats-meld-fund.html",
        menu=list_of_stats,
        marker="meldungen_meld_fund",
        user_id=session["user_id"],
        trace1=res_trace1,
        trace2=res_trace2,
    )
