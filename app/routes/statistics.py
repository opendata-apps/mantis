import json
from flask import Blueprint
from flask import render_template, request
from flask import session, abort
from sqlalchemy import text
from app import db
from app.database.models import TblUsers
from functools import wraps

stats = Blueprint("statistics", __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


list_of_stats = {
    "xxx": "Bitte eine Wahl treffen...",
    "start": "Statistik: Startseite",
    "geschlecht": "Entwicklungsstadium/Geschlecht",
    "meldungen_pro_woche": "Meldungen nach Datum",
}


@stats.route("/statistik", methods=["POST"])
@stats.route("/statistik/<usrid>", methods=["GET"])
def stats_start(usrid=None):
    "Startseite für alle Statistiken"

    if request.form:
        usrid = request.form.get('userId', '0')

    user = TblUsers.query.filter_by(user_id=usrid).first()

    # If the user doesn't exist or the role isn't 9, return 404
    if not user or user.user_rolle != '9':
        abort(403)

    value = request.form.get('stats', 'start')
    if value == "geschlecht":
        return stats_geschlecht()
    elif value == "meldungen_pro_woche":
        return stats_meldungen_woche()
    elif value == "start":
        return render_template("statistics/statistiken.html",
                               menu=list_of_stats,
                               marker="start")
    else:
        return render_template("statistics/statistiken.html",
                               menu=list_of_stats,
                               marker="start")


def stats_geschlecht(request=None):
    "Count sum of all kategories"

    sql = text('''
      select  sum(art_o) as "Ootheken"
            , sum(art_n) as "Nymphen"
            , sum(art_w) as "Weibchen"
            , sum(art_m) as "Männchen"
            , sum(art_f) as "Andere"
            , sum(tiere) as "tiere"
      from meldungen
      where deleted is NULL;
    ''')

    with db.engine.connect() as conn:
        result = conn.execute(sql)
        for row in result:
            row = row._mapping
            res = dict((name, val) for name, val in row.items())

#        rows = {'x': ['Ootheken', 'Nymphen', 'Weibchen',
#                      'Männchen', 'Andere', 'Summe'],
#                'y': [10, 1000, 1100, 2000, 20, 4140]
#                }
        
    return render_template("statistics/stats-geschlecht.html",
                           menu=list_of_stats,
                           marker="geschlecht",
                           values=res)


def stats_meldungen_woche(request=None):
    "Cluster messages per week"

#    dbsession = db.engine.connect()
    sql = text(""" SELECT extract(week from dat_meld) as Week,
                   count(dat_meld) as Anzahl
                   FROM meldungen
                   GROUP BY Week
                   ORDER by Week;""")
    with db.engine.connect() as conn:
        result = conn.execute(sql)

    trace1 = {"x": [],
              "y": []}

    if result:
        for record in result:
            trace1['x'].append(record[0])
            trace1['y'].append(record[1])
        else:
            pass
    res = json.loads(json.dumps(trace1))

    return render_template("statistics/stats-wochen.html",
                           menu=list_of_stats,
                           marker="meldungen_pro_woche",
                           values=res)
