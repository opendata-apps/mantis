# from app.database.models import Mantis
import json
import os
import random
from flask import (
    Blueprint,
    Response,
    current_app,
    jsonify,
    render_template,
    request,
    send_from_directory,
    session,
)

from datetime import date
from sqlalchemy import select, func, text
from app import db
from app.database.models import TblMeldungen, ReportStatus
from app.tools.check_reviewer import login_required


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Blueprints
main = Blueprint("main", __name__)


@main.route("/")
@main.route("/start")
def index():
    "Index page."
    count_stmt = (
        select(func.count())
        .select_from(TblMeldungen)
        .where(TblMeldungen.dat_fund_von >= date(current_app.config["MIN_MAP_YEAR"], 1, 1))
        .where(TblMeldungen.statuses.contains([ReportStatus.APPR.value]))
    )
    post_count = db.session.execute(count_stmt).scalar()

    celebration_enabled = check_celebration_flag(post_count)

    json_path = os.path.join(
        BASE_DIR, "..", "static", "images", "galerie", "galerie.json"
    )
    with open(json_path, "r", encoding="utf-8") as file:
        bilder = json.load(file)

    current_index = int(
        request.args.get("current_index", random.randint(0, len(bilder) - 1))
    )

    return render_template(
        "home.html",
        post_count=post_count,
        bilder=bilder,
        current_index=current_index,
        celebration_enabled=celebration_enabled,
        celebration_threshold=current_app.config["CELEBRATION_THRESHOLD"],
    )


@main.route("/health")
def health():
    """Health check endpoint."""
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "healthy"})
    except Exception:
        return jsonify({"status": "unhealthy"}), 503


def check_celebration_flag(post_count):
    if post_count <= current_app.config["CELEBRATION_THRESHOLD"]:
        return False
    return True


def styles():
    "Return the theme.css file."
    return send_from_directory("static/build", "theme.css")


@main.route("/faq")
def faq():
    "Frequently asked questions."
    return render_template("faq.html")


@main.route("/impressum")
def impressum():
    "Impressum."
    return render_template("impressum.html")


@main.route("/lizenz")
def lizenz():
    "Lizenz."
    return render_template("lizenz.html")


@main.route("/datenschutz")
def datenschutz():
    "Datenschutz."
    return render_template("datenschutz.html")


@main.route("/mantis-religiosa")
def mantis_religiosa():
    "Mantis religiosa info Page."
    return render_template("mantis_religiosa.html")


@main.route("/bestimmung")
def bestimmung():
    "Help for Bestimmung."
    return render_template("bestimmung.html")


@main.route("/sitemap.xml")
def sitemap():
    "Return the sitemap.xml file."
    with current_app.open_resource("static/sitemap.xml") as f:
        content = f.read()
    return Response(content, mimetype="application/xml")


@main.route("/robots.txt")
def robots():
    "Return the robots.txt file."
    with current_app.open_resource("static/robots.txt") as f:
        content = f.read()
    return Response(content, mimetype="text/plain")


@main.route("/galerie")
@login_required
def galerie():
    "Galerie."
    json_path = os.path.join(
        BASE_DIR, "..", "static", "images", "galerie", "galerie.json"
    )
    with open(json_path, "r", encoding="utf-8") as file:
        bilder = json.load(file)

    current_index = int(
        request.args.get("current_index", random.randint(0, len(bilder) - 1))
    )

    return render_template(
        "galerie.html",
        user_id=session["user_id"],
        bilder=bilder,
        current_index=current_index,
    )


@main.route("/favicon.ico")
def favicon():
    "Return the favicon.ico file."
    return send_from_directory("static", "images/favicon/favicon.ico")


def not_found(e):
    "404 error page."
    return render_template("404.html")
