from flask import jsonify, render_template, request, Blueprint, send_from_directory
from app import db
# from app.database.models import Mantis
import json
from app.database.models import TblMeldungen, TblFundortBeschreibung, TblFundorte, TblMeldungUser, TblPlzOrt, TblUsers
from datetime import datetime
from app.forms import MantisSightingForm
from sqlalchemy import or_
from flask import render_template_string
from sqlalchemy import inspect

# Blueprints
admin = Blueprint('admin', __name__)


@admin.route('/admin')
def admin_index():
    reported_sightings = TblMeldungen.query.all()
    return render_template('admin/adminPanel.html', reported_sightings=reported_sightings)


@admin.route('/admin/log')
def admin_subsites_log():
    return render_template('admin/log.html')


@admin.route('/admin/userAdministration')
def admin_subsites_users():
    return render_template('admin/userAdministration.html')

@admin.route('/admin/export/db2csv')
def admin_export_csv():

    reports = TblMeldungen.query.join(
        TblFundorte, TblMeldungen.fo_zuordnung == TblFundorte.id).all()
    return render_template('admin/userAdministration.html')
