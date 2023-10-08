from flask import jsonify, render_template, request, Blueprint, send_from_directory
import json

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

    rows = {'x': ['Ootheken', 'Nymphen','Weibchen', 'Männchen', 'Andere','Summe'],
            'y': [10, 1000, 1100, 2000, 20, 4140]
    }

    return render_template("statistics/stats-geschlecht.html",
                           menu=list_of_stats,
                           values=rows)
