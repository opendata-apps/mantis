from flask import jsonify, render_template, request, Blueprint, send_from_directory
from app import db
# from app.database.models import Mantis
import json
from app.database.models import TblMeldungen, TblFundortBeschreibung, TblFundorte, TblMeldungUser, TblPlzOrt, TblUsers
from datetime import datetime
from app.forms import MantisSightingForm
from sqlalchemy import or_

# Blueprints
admin = Blueprint('admin', __name__)


@admin.route('/admin')
def admin_index():
    return render_template('admin/adminPanel.html')

@admin.route('/admin/log')
def admin_subsites_log():
    return render_template('admin/log.html')

@admin.route('/admin/userAdministration')
def admin_subsites_users():
    return render_template('admin/userAdministration.html')
