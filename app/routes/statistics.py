from flask import jsonify, render_template, request, Blueprint, send_from_directory

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
