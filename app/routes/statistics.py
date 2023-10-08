import json
from flask import Blueprint, send_from_directory
from flask import jsonify, render_template, request
from sqlalchemy import text
from app import db

stats = Blueprint("statstics", __name__)

list_of_stats = {
    "geschlecht": "Entwicklungsstadium/Geschlecht",
    "povider": "Anzahl Melder",
    "timescale": "Meldungen nach Datum",
    "imagesize": "Bildgröße [KB] (Durchschnitt)",
}


@stats.route("/statistik")
def stats_start():
    "Startseite für alle Statistiken"

    return render_template("statistics/statistiken.html", menu=list_of_stats)

@stats.route("/statistik/geschlecht")
def stats_geschlecht():
    "Count sum of all kategories"

    sql = text(f'''
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
    print(res)
    rows = {'x': ['Ootheken', 'Nymphen','Weibchen', 'Männchen', 'Andere','Summe'],
            'y': [10, 1000, 1100, 2000, 20, 4140]
    }

    return render_template("statistics/stats-geschlecht.html",
                           menu=list_of_stats,
                           values=res)
