from datetime import datetime
from pathlib import Path
from PIL import Image

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from sqlalchemy import or_
from werkzeug.utils import secure_filename

from app import db
from app.database.models import TblFundortBeschreibung, TblFundorte, TblMeldungUser, TblMeldungen, TblPlzOrt, TblUsers
from app.forms import MantisSightingForm
from app.tools.gen_user_id import get_new_id
import os
import json

# Blueprints
data = Blueprint('data', __name__)

# Flask application and routes
UPLOAD_FOLDER = 'app/datastore'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def _create_directory(date):
    dir_path = os.path.join(UPLOAD_FOLDER, date)
    Path(dir_path).mkdir(parents=True, exist_ok=True)
    return dir_path


def _create_filename(location, usrid):
    return '{}-{}.webp'.format(location, usrid)


def _allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _update_or_create_user(usrid, last_name, first_name, contact):
    existing_user = TblUsers.query.filter_by(user_id=usrid).first()

    if existing_user is None:
        max_id = db.session.query(db.func.max(TblUsers.id)).scalar()
        new_user = TblUsers(user_id=usrid, user_name=f'{first_name} {last_name}', user_rolle=1, user_kontakt=contact)
        new_user.id = (max_id or 0) + 1
        db.session.add(new_user)
        db.session.flush()
        return new_user

    existing_user.user_name = f'{first_name} {last_name}'
    existing_user.user_kontakt = contact
    db.session.add(existing_user)
    db.session.flush()
    return existing_user



def _handle_file_upload(request, form, usrid):
    if 'picture' not in request.files:
        flash('No file part')
        return None
    file = request.files['picture']

    if file.filename == '' or not _allowed_file(file.filename):
        flash('No selected file')
        return None

    date_folder = _create_directory(
        form.sighting_date.data.strftime('%Y-%m-%d'))
    filename = _create_filename(form.city.data, usrid)
    full_file_path = os.path.join(date_folder, filename)

    # Convert image to webp and save
    img = Image.open(file)
    img.save(full_file_path, 'WEBP')

    return full_file_path


def _set_gender_fields(selected_gender):
    genders = {'art_m': 0, 'art_w': 0, 'art_n': 0, 'art_o': 0}
    gender_mapping = {'männchen': 'art_m', 'weibchen': 'art_w',
                      'nymphen': 'art_n', 'ootheken': 'art_o'}
    gender_field = gender_mapping.get(selected_gender)

    if gender_field:
        genders[gender_field] = 1

    return genders


def _user_to_dict(user):
    return {
        "user_name": user.user_name,
        "user_kontakt": user.user_kontakt,
    }


@data.route('/report', methods=['GET', 'POST'])
@data.route('/report/<usrid>', methods=['GET', 'POST'])
def report(usrid=None):
    existing_user = TblUsers.query.filter_by(user_id=usrid).first() if usrid else None
    if not existing_user:
        usrid = get_new_id()

    form = MantisSightingForm(userid=usrid)

    if existing_user and request.method == 'GET':
        form.process(obj=existing_user)
        form.report_first_name.render_kw = {"readonly": "readonly"}
        form.report_last_name.render_kw = {"readonly": "readonly"}
        form.contact.render_kw = {"readonly": "readonly"}

    if form.validate_on_submit():
        new_fundort_beschreibung = TblFundortBeschreibung(
            beschreibung=form.location_description.data)
        max_id = db.session.query(db.func.max(TblFundortBeschreibung.id)).scalar()
        new_fundort_beschreibung.id = (max_id or 0) + 1
        db.session.add(new_fundort_beschreibung)
        db.session.flush()

        bildpfad = _handle_file_upload(request, form, usrid)

        new_fundort = TblFundorte(plz=form.zip_code.data, ort=form.city.data, strasse=form.street.data,
                                  kreis=form.district.data, land=form.state.data, longitude=form.longitude.data,
                                  latitude=form.latitude.data, beschreibung=new_fundort_beschreibung.id, ablage=bildpfad)
        max_id = db.session.query(db.func.max(TblFundorte.id)).scalar()
        new_fundort.id = (max_id or 0) + 1
        db.session.add(new_fundort)
        db.session.flush()

        genders = _set_gender_fields(form.gender.data)

        new_meldung = TblMeldungen(dat_fund_von=form.sighting_date.data, dat_fund_bis=form.sighting_date.data,
                                   dat_meld=datetime.now(), fo_zuordnung=new_fundort.id, fo_quelle="F", **genders)
        max_id = db.session.query(db.func.max(TblMeldungen.id)).scalar()
        new_meldung.id = (max_id or 0) + 1
        db.session.add(new_meldung)
        db.session.flush()

        updated_user = _update_or_create_user(usrid, form.report_last_name.data, form.report_first_name.data,
                                              form.contact.data)
        max_id = db.session.query(db.func.max(TblUsers.id)).scalar()
        updated_user.id = (max_id or 0) + 1

        new_meldung_user = TblMeldungUser(id_meldung=new_meldung.id, id_user=updated_user.id)
        max_id = db.session.query(db.func.max(TblMeldungUser.id)).scalar()
        new_meldung_user.id = (max_id or 0) + 1
        db.session.add(new_meldung_user)
        db.session.commit()

        flash({
            'title': 'Vielen Dank für Ihre Meldung!',
            'message': 'Um weitere Meldungen zu machen, speichern Sie bitte die folgende ID:',
            'usrid': str(usrid),
        })

        return redirect(url_for('data.report'))

    print(form.errors)
    if existing_user is not None:
        existing_user = _user_to_dict(existing_user)
    return render_template('report.html', form=form, existing_user=existing_user)



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
