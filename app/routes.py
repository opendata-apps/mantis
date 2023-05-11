from flask import render_template, request, Blueprint, send_from_directory
from app import db
# from app.database.models import Mantis
import json
from app.database.models import TblMeldungen, TblFundortBeschreibung, TblFundorte, TblMeldungUser, TblPlzOrt, TblUsers
from datetime import datetime

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


@main.route('/auswertungen')
def auswertungen():
    return render_template('auswertungen.html')

# todo: new database


@main.route('/report', methods=['GET', 'POST'])
def report():
    return render_template('report.html')


@main.route('/map')
def show_map():
    # Fetch the reports data from the database
    reports = TblMeldungen.query.join(
        TblFundorte, TblMeldungen.fo_zuordung == TblFundorte.id).all()

    # Serialize the reports data as a JSON object
    reportsJson = json.dumps(
        [{'latitude': report.latitude, 'longitude': report.longitude} for report in reports])
    print(reportsJson)

    # Render the template with the serialized data
    return render_template('map.html', reportsJson=reportsJson)


@main.route('/statistics')
def statistics():
    mantis_count = TblMeldungen.query.count()
    return render_template('statistics.html', mantis_count=mantis_count)


@main.route('/faq')
def faq():
    return render_template('faq.html')


@main.route('/impressum')
def impressum():
    return render_template('impressum.html')


@main.route('/aboutUs')
def aboutUs():
    return render_template('aboutUs.html')


@main.route('/gitLab')
def gitLab():
    return render_template('gitLab.html')


@main.route('/lizenz')
def lizenz():
    return render_template('lizenz.html')


@main.route('/datenschutz')
def datenschutz():
    return render_template('datenschutz.html')


@main.route('/agb')
def agb():
    return render_template('agb.html')


@main.route('/reportanissue')
def report_an_issue():
    return render_template('reportAnIssue.html')


@main.route('/newitem')
def new_item():
    return render_template('new_item.html')


@main.route('/admin')
def admin():
    return render_template('admin.html')


@main.route('/admin/log')
def admin_subsites_log():
    return render_template('adminSubsites/log.html')


@main.route('/mantis')
def mantis():
    return render_template('mantis.html')
