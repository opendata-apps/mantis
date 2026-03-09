import json
import os
import time
from flask import (
    Blueprint,
    Response,
    current_app,
    g,
    jsonify,
    render_template,
    send_from_directory,
)

from datetime import date
from sqlalchemy import select, func, text
from app import db
from app.database.models import TblMeldungen, ReportStatus
from app.auth import login_required


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Cached static data ---

_galerie_cache = None


def _load_galerie():
    """Load and cache galerie.json (static file, read once)."""
    global _galerie_cache
    if _galerie_cache is None:
        json_path = os.path.join(
            BASE_DIR, "..", "static", "images", "galerie", "galerie.json"
        )
        with open(json_path, "r", encoding="utf-8") as file:
            _galerie_cache = json.load(file)
    return _galerie_cache


_sitemap_cache = None
_robots_cache = None


_post_count_cache = {"value": None, "timestamp": 0}

# Blueprints
main = Blueprint("main", __name__)


def _get_post_count():
    """Get approved post count with a 5-minute TTL cache."""
    now = time.monotonic()
    if _post_count_cache["value"] is not None and (now - _post_count_cache["timestamp"]) < 300:
        return _post_count_cache["value"]

    count_stmt = (
        select(func.count())
        .select_from(TblMeldungen)
        .where(TblMeldungen.dat_fund_von >= date(current_app.config["MIN_MAP_YEAR"], 1, 1))
        .where(TblMeldungen.statuses.contains([ReportStatus.APPR.value]))
    )
    value = db.session.execute(count_stmt).scalar()
    _post_count_cache["value"] = value
    _post_count_cache["timestamp"] = now
    return value


@main.route("/")
@main.route("/start")
def index():
    "Index page."
    post_count = _get_post_count()
    celebration_enabled = check_celebration_flag(post_count)
    bilder = _load_galerie()

    return render_template(
        "home.html",
        post_count=post_count,
        bilder=bilder,
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
    return post_count > current_app.config["CELEBRATION_THRESHOLD"]


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
    global _sitemap_cache
    if _sitemap_cache is None:
        with current_app.open_resource("static/sitemap.xml") as f:
            _sitemap_cache = f.read()
    return Response(_sitemap_cache, mimetype="application/xml")


@main.route("/robots.txt")
def robots():
    "Return the robots.txt file."
    global _robots_cache
    if _robots_cache is None:
        with current_app.open_resource("static/robots.txt") as f:
            _robots_cache = f.read()
    return Response(_robots_cache, mimetype="text/plain")


@main.route("/galerie")
@login_required
def galerie():
    "Galerie."
    return render_template(
        "galerie.html",
        user_id=g.current_user.user_id,
        bilder=_load_galerie(),
    )


@main.route("/favicon.ico")
def favicon():
    "Return the favicon.ico file."
    return send_from_directory("static", "images/favicon/favicon.ico")

