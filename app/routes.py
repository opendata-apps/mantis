from flask import render_template, request, Blueprint, send_from_directory
from app import db
# from app.database.models import Mantis
import json
import app.database.models


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
    if request.method == 'POST':
        # get form data and save to database
        latitude = request.form['latitude']
        longitude = request.form['longitude']
        photo_url = request.form['photo_url']
        mantis = Mantis(latitude=latitude, longitude=longitude,
                        photo_url=photo_url)
        db.session.add(mantis)
        db.session.commit()
    return render_template('report.html')

# todo: new database


@main.route('/map')
def show_map():
    # Fetch the reports data from the database
    reports = Mantis.query.all()

    # Serialize the reports data as a JSON object
    reportsJson = json.dumps([report.to_dict() for report in reports])
    print(reportsJson)

    # Render the template with the serialized data
    return render_template('map.html', reportsJson=reportsJson)

# todo: new database


@main.route('/statistics')
def statistics():
    mantis_count = Mantis.query.count()
    return render_template('statistics.html', mantis_count=mantis_count)


@main.route('/faq')
def faq():
    return render_template('faq.html')


@main.route('/impressum')
def impressum():
    return render_template('impressum.html')


@main.route('/about')
def about():
    return render_template('about.html')


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
