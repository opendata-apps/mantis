from flask import jsonify, render_template, request, Blueprint, send_from_directory
from app import db
# from app.database.models import Mantis
import json
from app.database.models import TblMeldungen, TblFundortBeschreibung, TblFundorte, TblMeldungUser, TblPlzOrt, TblUsers
from datetime import datetime
from app.forms import MantisSightingForm
from sqlalchemy import or_
from flask_sqlalchemy import SQLAlchemy


# Blueprints
main = Blueprint('main', __name__)


@main.route('/start')
@main.route('/')
def index():
    post_count = db.session.query(TblMeldungen).count()
    return render_template('home.html', post_count=post_count)


@main.route('/static/build/theme.css')
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