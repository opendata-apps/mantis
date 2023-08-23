from flask import jsonify, render_template, request, Blueprint, send_from_directory
from app import db
# from app.database.models import Mantis
import json
from app.database.models import TblMeldungen, TblFundortBeschreibung, TblFundorte, TblMeldungUser, TblUsers
from datetime import datetime
from app.forms import MantisSightingForm
from sqlalchemy import or_
from flask_sqlalchemy import SQLAlchemy
from flask import flash, redirect, url_for
from flask import render_template, send_from_directory
import random
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Blueprints
main = Blueprint('main', __name__)


@main.route('/start')
@main.route('/')
def index():
    post_count = db.session.query(TblMeldungen).count()
    return render_template('home.html', post_count=post_count)

import time


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



@main.route('/gallerie')
def gallerie():
    json_path = os.path.join(BASE_DIR, '..', 'datastore', 'gallerie', 'gallerie.json')
    with open(json_path, 'r', encoding='utf-8') as file:
        bilder = json.load(file)
        
    current_index = int(request.args.get('current_index', random.randint(0, len(bilder) - 1)))
    
    return render_template('gallerie.html', bilder=bilder, current_index=current_index)

@main.route('/gallerie-navigation/<direction>')
def gallerie_navigation(direction):
    json_path = os.path.join(BASE_DIR, '..', 'datastore', 'gallerie', 'gallerie.json')
    with open(json_path, 'r', encoding='utf-8') as file:
        bilder = json.load(file)
    
    current_index = int(request.args.get('current_index', 0))
    
    if direction == 'left':
        current_index = (current_index - 1) % len(bilder)
    elif direction == 'right':
        current_index = (current_index + 1) % len(bilder)
    
    return redirect(url_for('main.gallerie', current_index=current_index))

@main.route('/gallerie-bilder/<filename>')
def gallerie_bilder(filename):
    bilder_directory = os.path.join(BASE_DIR, '..', 'datastore', 'gallerie')
    return send_from_directory(bilder_directory, filename)


def not_found(e):
    return render_template("404.html")
