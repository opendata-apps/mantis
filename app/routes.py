from flask import render_template, request
from app import app, db
from app.database.models import Mantis
import json
# from app.models import Mantis


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/static/build/theme.css')
def styles():
    return app.send_static_file('build/theme.css')


@app.route('/report', methods=['GET', 'POST'])
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


@app.route('/map')
def show_map():
    # Fetch the reports data from the database
    reports = Mantis.query.all()

    # Serialize the reports data as a JSON object
    reportsJson = json.dumps([report.to_dict() for report in reports])
    print(reportsJson)

    # Render the template with the serialized data
    return render_template('map.html', reportsJson=reportsJson)


@app.route('/statistics')
def statistics():
    mantis_count = Mantis.query.count()
    return render_template('statistics.html', mantis_count=mantis_count)


@app.route('/faq')
def faq():
    return render_template('faq.html')


@app.route('/impressum')
def impressum():
    return render_template('impressum.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/reportanissue')
def report_an_issue():
    return render_template('report_an_issue.html')


@app.route('/newitem')
def new_item():
    return render_template('new_item.html')


@app.route('/admin')
def admin():
    return render_template('admin.html')


@app.route('/admin/log')
def admin_subsites_log():
    return render_template('adminSubsites/log.html')


@app.route('/mantis')
def mantis():
    return render_template('mantis.html')
