# from app.database.models import Mantis
import json
import os
import random
from datetime import datetime, timedelta

from flask import (
    Blueprint,
    Response,
    current_app,
    render_template,
    request,
    send_from_directory,
    session,
)

from app import db
from app.database.models import TblMeldungen
from app.tools.check_reviewer import login_required

from ..config import Config

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FEATURE_FLAG_FILE = os.path.join(BASE_DIR, '..', 'static', 'celebration_flag.json')

# Blueprints
main = Blueprint("main", __name__)


@main.route("/")
@main.route("/start")
def index():
    "Index page."
    post_count = (
        db.session.query(TblMeldungen)
        .filter(TblMeldungen.dat_fund_von >= f"{Config.MIN_MAP_YEAR}-01-01")
        .filter(TblMeldungen.dat_bear != None)
        .filter(TblMeldungen.deleted.is_(None))
        .count()
    )
    
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
    )
    
def check_celebration_flag(post_count):
    if post_count <= 10000:
        return False
    
    if not os.path.exists(FEATURE_FLAG_FILE):
        set_celebration_flag()
        return True
    
    with open(FEATURE_FLAG_FILE, 'r') as f:
        flag_data = json.load(f)
    
    if datetime.now() > datetime.fromisoformat(flag_data['expiry']):
        return False
    
    return True


def set_celebration_flag():
    expiry = (datetime.now() + timedelta(days=1)).isoformat()
    flag_data = {'expiry': expiry}
    
    os.makedirs(os.path.dirname(FEATURE_FLAG_FILE), exist_ok=True)
    with open(FEATURE_FLAG_FILE, 'w') as f:
        json.dump(flag_data, f)



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


def not_found(e):
    "404 error page."
    return render_template("404.html")