from flask import jsonify, render_template, request, Blueprint, send_from_directory
from app import db
# from app.database.models import Mantis
import json
from app.database.models import TblMeldungen, TblFundortBeschreibung, TblFundorte, TblMeldungUser, TblPlzOrt, TblUsers
from datetime import datetime
from app.forms import MantisSightingForm
from sqlalchemy import or_

# Blueprints
main = Blueprint('main', __name__)


@main.route('/')
def index():
    return render_template('home.html')


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

# TODO: Remove this route its Projekt


@main.route('/aboutUs')
def aboutUs():
    return render_template('aboutUs.html')


@main.route('/lizenz')
def lizenz():
    return render_template('lizenz.html')


@main.route('/datenschutz')
def datenschutz():
    return render_template('datenschutz.html')
