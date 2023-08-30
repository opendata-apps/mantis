import time
from flask import jsonify
from flask import render_template
from flask import request
from flask import Blueprint
from flask import send_from_directory
from app import db
# from app.database.models import Mantis
import json
from app.database.models import TblMeldungen
from app.database.models import TblFundortBeschreibung
from app.database.models import TblFundorte
from app.database.models import TblMeldungUser
from app.database.models import TblUsers
from datetime import datetime
from app.forms import MantisSightingForm
from sqlalchemy import or_
from flask_sqlalchemy import SQLAlchemy
from flask import flash, redirect, url_for
from flask import current_app
from flask import Response

# Blueprints
main = Blueprint('main', __name__)


@main.route('/start')
@main.route('/')
def index():
    post_count = db.session.query(TblMeldungen).filter(
        TblMeldungen.deleted == None).count()

    return render_template('home.html', post_count=post_count)


def styles():
    return send_from_directory('static/build', 'theme.css')


@main.route('/projekt')
def projekt():
    return render_template('projekt.html')


@main.route('/faq')
def faq():
    return render_template('faq.html')


@main.route('/impressum')
def impressum():
    return render_template('impressum.html')


@main.route('/lizenz')
def lizenz():
    return render_template('lizenz.html')


@main.route('/datenschutz')
def datenschutz():
    return render_template('datenschutz.html')


@main.route('/mantis-religiosa')
def mantis_religiosa():
    return render_template('mantis_religiosa.html')


@main.route('/bestimmung')
def bestimmung():
    return render_template('bestimmung.html')


@main.route('/sitemap.xml')
def sitemap():
    with current_app.open_resource('static/sitemap.xml') as f:
        content = f.read()
    return Response(content, mimetype='application/xml')


@main.route('/robots.txt')
def robots():
    with current_app.open_resource('static/robots.txt') as f:
        content = f.read()
    return Response(content, mimetype='text/plain')


def not_found(e):
    return render_template("404.html")
