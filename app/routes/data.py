from datetime import datetime
from pathlib import Path
from PIL import Image

from flask import Blueprint, flash, jsonify, redirect
from flask import render_template, request, url_for
from sqlalchemy import or_
from werkzeug.utils import secure_filename
from werkzeug.datastructures import CombinedMultiDict

from app import db
from app.database.models import TblFundortBeschreibung
from app.database.models import TblFundorte, TblMeldungUser
from app.database.models import TblMeldungen, TblUsers
from app.forms import MantisSightingForm
from app.tools.gen_user_id import get_new_id
import os
import json
import copy
from app.tools.send_email import send_email

from ..config import Config
# Blueprints
data = Blueprint('data', __name__)
checklist = Config.CHECKLIST

# Flask application and routes
def _create_directory(date):
    current_year = datetime.now().strftime("%Y")
    dir_path = Path(Config.UPLOAD_FOLDER + "/" + current_year + "/" + date)
    dir_path.mkdir(parents=True, exist_ok=True)
    ablage_path = current_year + "/" + date
    return dir_path


def _create_filename(location, usrid):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return '{}-{}-{}.webp'.format(secure_filename(location),
                                  timestamp,
                                  secure_filename(usrid))


def _allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def _update_or_create_user(usrid, finderid, last_name, first_name, contact, finder_last_name, finder_first_name):
    existing_user = TblUsers.query.filter_by(user_id=usrid).first()
    # existing_finder = TblUsers.query.filter_by(
    #     user_id=usrid).filter_by(user_rolle="2").first()

    new_finder = None
    if finder_first_name and finder_last_name:
        new_finder = TblUsers(
            user_id=finderid,
            user_name=finder_last_name + " " + finder_first_name[0] + ".",
            user_rolle=2,
        )
        db.session.add(new_finder)
        db.session.flush()

    if not existing_user:
        new_user = TblUsers(
            user_id=usrid,
            user_name=last_name + " " + first_name[0] + ".",
            user_rolle=1,
            user_kontakt=contact,
        )
        db.session.add(new_user)
        db.session.flush()
        return new_user, new_finder
    return existing_user, new_finder


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
    full_file_path = date_folder / filename

    # Convert image to webp and save
    img = Image.open(file)
    img.save(str(full_file_path), 'WEBP')

    # return the path as string with forward slashes
    return str(full_file_path.as_posix())


def _set_gender_fields(selected_gender):
    genders = {'art_m': 0, 'art_w': 0, 'art_n': 0, 'art_o': 0}
    gender_mapping = {'Männchen': 'art_m', 'Weibchen': 'art_w',
                      'Nymphe': 'art_n', 'Oothek': 'art_o'}
    gender_field = gender_mapping.get(selected_gender)

    if gender_field:
        genders[gender_field] = 1

    return genders


def _user_to_dict(user):
    return {
        "user_name": user.user_name,
        "user_kontakt": user.user_kontakt,
    }


def _saveip(ip):
    "Manage IP's to control allow only one report/day"
    global checklist
    if  ip  not in checklist:
      checklist[ip] = 0
    else:
        checklist[ip] += 1
    return

@data.route('/report', methods=['GET', 'POST'])
@data.route('/report/<usrid>', methods=['GET', 'POST'])
def report(usrid=None):
    # check ip 
    global checklist
    ip = request.remote_addr
    pid = os.getpid()
    mark = f"{ip}:{pid}"
    _saveip(mark)
    if checklist.get(mark) > 2:
        return redirect(url_for('main.index'))
    finderid = get_new_id()
    existing_user = TblUsers.query.filter_by(
        user_id=usrid).first() if usrid else None
    if not existing_user:
        usrid = get_new_id()

    form = MantisSightingForm(userid=usrid, meta={'locales': ['de_DE', 'de']})

    if existing_user and request.method == 'GET':
        form.process(obj=existing_user)
        form.report_first_name.render_kw = {"readonly": "readonly"}
        form.report_last_name.render_kw = {"readonly": "readonly"}
        form.contact.render_kw = {"readonly": "readonly"}

    if form.validate_on_submit():

        bildpfad = _handle_file_upload(request, form, usrid).replace(
            Config.UPLOAD_FOLDER + "/", "")

        new_fundort = TblFundorte(plz=form.zip_code.data,
                                  ort=form.city.data,
                                  strasse=form.street.data,
                                  kreis=form.district.data,
                                  land=form.state.data,
                                  longitude=form.longitude.data,
                                  latitude=form.latitude.data,
                                  beschreibung=int(
                                      form.location_description.data),
                                  ablage=bildpfad)
        db.session.add(new_fundort)
        db.session.flush()

        genders = _set_gender_fields(form.gender.data)

        new_meldung = TblMeldungen(dat_fund_von=form.sighting_date.data,
                                   dat_meld=datetime.now(),
                                   fo_zuordnung=new_fundort.id,
                                   fo_quelle="F",
                                   art_f='0',
                                   tiere='1',
                                   **genders,
                                   anm_melder=form.picture_description.data)
        db.session.add(new_meldung)
        db.session.flush()

        updated_user, updated_finder = _update_or_create_user(usrid,
                                                              finderid,
                                                              form.report_last_name.data,
                                                              form.report_first_name.data,
                                                              form.contact.data,
                                                              form.finder_first_name.data,
                                                              form.finder_last_name.data,
                                                              )

        if updated_finder:
            new_meldung_user = TblMeldungUser(
                id_meldung=new_meldung.id, id_user=updated_user.id, id_finder=updated_finder.id)
        else:
            new_meldung_user = TblMeldungUser(
                id_meldung=new_meldung.id, id_user=updated_user.id)

        db.session.add(new_meldung_user)
        db.session.commit()

        flash({
            'title': 'Daten wurden gesendet.',
            'message': 'Vielen Dank für Ihre Meldung!',
        })
        addresse = form.contact.data

        if Config.send_emails and addresse:
           send_email(formdata=form)

        return redirect(url_for('data.report', usrid=usrid))

    if existing_user is not None:
        existing_user = _user_to_dict(existing_user)
    return render_template('report.html',
                           form=form,
                           existing_user=existing_user,
                           apikey=Config.esri,)


@data.route('/validate', methods=['POST'])
def validate():
    form_data = CombinedMultiDict(
        (request.form, request.files))  # type: ignore
    form = MantisSightingForm(form_data)

    if form.validate():
        return jsonify({'success': True})
    else:
        return jsonify({'errors': form.errors}), 333


@data.route('/auswertungen')
def show_map():

    # Summe aller Meldungen für den Counter
    post_count = db.session.query(TblMeldungen).count()

    # Fetch the reports data from the database where dat_bear
    # is not null in TblMeldungen
    # TblMeldungen, TblMeldungen.fo_zuordnung == \
    # TblFundorte.id).filter(TblMeldungen.dat_bear != None).all()
    # Im Testmodus alle Meldungen anzeigen

    reports = TblFundorte.query.join(
        TblMeldungen, TblMeldungen.fo_zuordnung ==
        TblFundorte.id).filter(TblMeldungen.dat_bear != None).all()
    # Serialize the reports data as a JSON object
    koords = []
    for report in reports:
        try:
            lati = float(report.latitude.replace(',', '.'))
            long = float(report.longitude.replace(',', '.'))
            koords.append({'latitude': lati,
                           'longitude': long})
        except:
            pass

    reportsJson = json.dumps(koords)
    return render_template('map.html',
                           reportsJson=reportsJson,
                           apikey=Config.esri,
                           post_count=post_count)
