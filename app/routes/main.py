# from app.database.models import Mantis
import json
import time
from datetime import datetime

from flask import (Blueprint, Response, current_app, flash, jsonify, redirect,
                   render_template, request, send_from_directory, url_for)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_

from app import db
from app.database.models import (TblFundortBeschreibung, TblFundorte,
                                 TblMeldungen, TblMeldungUser, TblUsers)
from app.forms import MantisSightingForm

# Blueprints
main = Blueprint('main', __name__)


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
