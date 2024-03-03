# from app.database.models import Mantis
import json
import os
import random
from app import db
from app.database.models import TblMeldungen
from flask import (
    Blueprint,
    Response,
    current_app,
    render_template,
    request,
    send_from_directory,
)
from app.tools.check_reviewer import login_required
from flask import session

from ..config import Config

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Blueprints
main = Blueprint("main", __name__)


@main.route("/")
@main.route("/start")
def index():
    post_count = (
        db.session.query(TblMeldungen).filter(TblMeldungen.deleted == None).count()
    )
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
        current_year=Config.CURRENT_YEAR
    )


def styles():
    return send_from_directory("static/build", "theme.css")


@main.route("/projekt")
def projekt():
    return render_template("projekt.html")


@main.route("/faq")
def faq():
    return render_template("faq.html")


@main.route("/impressum")
def impressum():
    return render_template("impressum.html")


@main.route("/lizenz")
def lizenz():
    return render_template("lizenz.html")


@main.route("/datenschutz")
def datenschutz():
    return render_template("datenschutz.html")


@main.route("/mantis-religiosa")
def mantis_religiosa():
    return render_template("mantis_religiosa.html")


@main.route("/bestimmung")
def bestimmung():
    return render_template("bestimmung.html")


@main.route("/sitemap.xml")
def sitemap():
    with current_app.open_resource("static/sitemap.xml") as f:
        content = f.read()
    return Response(content, mimetype="application/xml")


@main.route("/robots.txt")
def robots():
    with current_app.open_resource("static/robots.txt") as f:
        content = f.read()
    return Response(content, mimetype="text/plain")


@main.route("/galerie")
@login_required
def galerie():
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
    return render_template("404.html")
