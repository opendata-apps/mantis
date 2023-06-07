from flask import jsonify, render_template, request, Blueprint, redirect, url_for, flash
from app import db
import json
from app.database.models import TblMeldungen
from app.database.models import TblFundorte
from app.database.models import TblPlzOrt
from app.database.models import TblUsers
from app.database.models import TblFundortBeschreibung
from app.database.models import TblMeldungUser
from app.forms import MantisSightingForm
from sqlalchemy import or_
from app.tools.gen_user_id import get_new_id
from flask import request
from werkzeug.utils import secure_filename
import os
from datetime import datetime

# Blueprints
data = Blueprint('data', __name__)


# Flask application and routes
UPLOAD_FOLDER = 'altes-lager/images/meldungen'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@data.route('/report', methods=['GET', 'POST'])
def report():
    usrid = get_new_id()
    form = MantisSightingForm(userid=usrid)

    if form.validate_on_submit():
        # Initialize all fields to 0
        art_m = 0
        art_w = 0
        art_n = 0
        art_o = 0

        # Set the appropriate field to 1 based on the gender
        if form.gender.data == 'männchen':
            art_m = 1
        elif form.gender.data == 'weibchen':
            art_w = 1
        elif form.gender.data == 'nymphen':
            art_n = 1
        elif form.gender.data == 'ootheken':
            art_o = 1

        new_fundort_beschreibung = TblFundortBeschreibung(
            beschreibung=form.location_description.data,
        )
        db.session.add(new_fundort_beschreibung)
        db.session.flush()  # This is needed to generate the ID

        # Check if the post request has the file part
        bildpfad = None
        if 'picture' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['picture']
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            bildpfad = os.path.join(UPLOAD_FOLDER, filename)

        new_fundort = TblFundorte(
            plz=form.zip_code.data,
            ort=form.city.data,
            strasse=form.street.data,
            kreis=form.district.data,
            land=form.state.data,
            longitude=form.longitude.data,
            latitude=form.latitude.data,
            beschreibung=new_fundort_beschreibung.id,
            ablage=bildpfad,
        )
        db.session.add(new_fundort)
        db.session.flush()  # This is needed to generate the ID

        new_meldung = TblMeldungen(
            dat_fund_von=form.sighting_date.data,
            dat_fund_bis=form.sighting_date.data,
            dat_meld=datetime.now(),
            fo_zuordnung=new_fundort.id,
            fo_quelle="F",
            art_m=art_m,
            art_w=art_w,
            art_n=art_n,
            art_o=art_o,
        )
        db.session.add(new_meldung)
        db.session.flush()  # This is needed to generate the ID

        new_user = TblUsers(
            user_id=usrid,
            user_name=form.report_last_name.data + " " +
            form.report_first_name.data[0] + ".",
            user_rolle=1,
            user_kontakt=form.contact.data,
        )
        db.session.add(new_user)
        db.session.flush()  # This is needed to generate the ID

        new_meldung_user = TblMeldungUser(
            id_meldung=new_meldung.id,
            id_user=new_user.id,
        )
        db.session.add(new_meldung_user)
        db.session.commit()
        
        flash('Vielen Dank für Ihre Meldung! Um weitere Meldungen zu machen, speichern Sie bitte die ID: ' + str(usrid) + ' ab.')

        return redirect(url_for('data.report'))
    
    print(form.errors)
    return render_template('report.html', form=form)


@data.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('q')
    results = db.session.query(TblPlzOrt).filter(
        or_(
            TblPlzOrt.plz.startswith(query),
            TblPlzOrt.ort.startswith(query),
            TblPlzOrt.landkreis.startswith(query),
            TblPlzOrt.bundesland.startswith(query)
        )
    ).limit(10).all()

    suggestions = []
    for result in results:
        suggestions.append({
            'plz': result.plz,
            'ort': result.ort,
            'landkreis': result.landkreis,
            'bundesland': result.bundesland
        })

    return jsonify(suggestions)


@data.route('/auswertungen')
def show_map():
    # Fetch the reports data from the database
    reports = TblFundorte.query.join(
        TblMeldungen, TblMeldungen.fo_zuordnung == TblFundorte.id).all()
    # Serialize the reports data as a JSON object
    reportsJson = json.dumps(
        [{'latitude': report.latitude.replace(',', '.'),
          'longitude': report.longitude.replace(',', '.')}
         for report in reports])
    # Render the template with the serialized data
    return render_template('map.html', reportsJson=reportsJson)


@data.route('/statistics')
def statistics():
    mantis_count = TblMeldungen.query.count()
    return render_template('statistics.html', mantis_count=mantis_count)
