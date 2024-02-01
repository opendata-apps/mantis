import json
from flask import Blueprint
from flask import render_template, request
from flask import session, abort
from sqlalchemy import text
from app import db
from app.database.models import TblUsers
from app.tools.check_reviewer import login_required

stats = Blueprint("statistics", __name__)

list_of_stats = {
    "xxx": "Bitte eine Wahl treffen ...",
    "start": "Statistik: Startseite",
    "geschlecht": "Entwicklungsstadium/Geschlecht",
    "meldungen_pro_tag": "Meldungen nach Datum",
}


@stats.route("/statistik", methods=["POST"])
@stats.route("/statistik/<usrid>", methods=["GET"])
@login_required
def stats_start(usrid=None):
    "Startseite für alle Statistiken"
    user_id = session['user_id']
    user = TblUsers.query.filter_by(user_id=user_id).first()

    # If the user doesn't exist or the role isn't 9, return 404
    if not user or user.user_rolle != '9':
        abort(403)

    value = request.form.get('stats', 'start')
    if value == "geschlecht":
        return stats_geschlecht()
    elif value == "meldungen_pro_tag":
        return stats_meldungen_tag()
    elif value == "start":
        return render_template("statistics/statistiken.html",
                               user_id=session['user_id'],
                               menu=list_of_stats,
                               marker="start")
    else:
        return render_template("statistics/statistiken.html",
                               user_id=session['user_id'],
                               menu=list_of_stats,
                               marker="start")


def stats_geschlecht(request=None):
    "Count sum of all kategories"

    sql = text('''
      select sum(art_m) as "Männchen"
            , sum(art_w) as "Weibchen"
            , sum(art_n) as "Nymphen"
            , sum(art_o) as "Ootheken"
            , sum(art_f) as "Andere"
      from meldungen
      where deleted is NULL;
    ''')

    with db.engine.connect() as conn:
        result = conn.execute(sql)
        res = []
        for row in result:
            row = row._mapping
            res = dict((name, val) for name, val in row.items())

    return render_template("statistics/stats-geschlecht.html",
                           menu=list_of_stats,
                           user_id=session['user_id'],
                           marker="geschlecht",
                           values=res)


def stats_meldungen_tag(request=None):
    "Cluster messages per day"

#    dbsession = db.engine.connect()
    sql = text(""" SELECT dat_meld as Tag,
                   count(dat_meld) as Anzahl
                   FROM meldungen
                   GROUP BY Tag
                   ORDER by Tag;""")
    with db.engine.connect() as conn:
        result = conn.execute(sql)

    trace1 = {"x": [],
              "y": []}

    if result:
        for record in result:
            trace1['x'].append(str(record[0]))
            trace1['y'].append(record[1])
        else:
            pass
    res = json.loads(json.dumps(trace1))

    return render_template("statistics/stats-tag.html",
                           menu=list_of_stats,
                           marker="meldungen_pro_tag",
                           user_id=session['user_id'],
                           values=res)
