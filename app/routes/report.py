import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from random import uniform
import string
from PIL import Image
import io

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
    abort,
    session,
    make_response
)
from werkzeug.datastructures import CombinedMultiDict, MultiDict
from werkzeug.utils import secure_filename

from app import db
from app.database.models import (TblFundorte,
                                 TblMeldungen,
                                 TblMeldungUser,
                                 TblUsers)
from app.forms import MantisSightingForm
from app.tools.gen_user_id import get_new_id
from app.tools.mtb_calc import get_mtb, pointInRect
from app.tools.find_gemeinde import get_amt_full_scan
import random
from ..config import Config

# Blueprints
report = Blueprint("report", __name__)

# For rate limiting - similar to checklist in data.py
report_submission_checklist = {}

def _check_and_update_ip_submission_count(ip_address: str, limit: int = 7) -> bool:
    """Checks and updates submission count for an IP. Returns True if limit exceeded."""
    global report_submission_checklist
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Check if we need to reset the checklist for a new day
    if report_submission_checklist.get("date") != today_str:
        report_submission_checklist = {"date": today_str}
        print(f"--- Rate limiting checklist reset for new day: {today_str} ---")

    current_count = report_submission_checklist.get(ip_address, 0)
    current_count += 1
    report_submission_checklist[ip_address] = current_count
    print(f"--- IP {ip_address} submission count: {current_count} ---")

    return current_count > limit

# Helper function to determine gender fields for TblMeldungen
def _set_gender_fields(selected_gender_value):
    """
    Maps a gender string to a dictionary of TblMeldungen gender fields.
    Example input: "Männlich", "Weibchen", etc.
    """
    genders = {"art_m": 0, "art_w": 0, "art_n": 0, "art_o": 0}
    gender_mapping = {
        "Männlich": "art_m",
        "Weiblich": "art_w",
        "Nymphe": "art_n",
        "Oothek": "art_o",
        "Unbekannt": "art_u" # Assuming TblMeldungen has an art_u or similar for unknown
    }
    db_field_name = gender_mapping.get(selected_gender_value)
    if db_field_name:
        # Ensure the key exists in genders dict, especially if art_u is new
        if db_field_name not in genders and db_field_name == "art_u": 
            genders["art_u"] = 0 # Initialize if not present
        genders[db_field_name] = 1
    return genders

@report.route("/melden", methods=["GET", "POST"])
@report.route("/melden/<usrid>", methods=["GET", "POST"])
def melden(usrid=None):
    """Handle the report form submission using SQLAlchemy, including rate limiting and pre-filling."""
    form = MantisSightingForm()
    user_prefilled_data = False # Flag to indicate if form was pre-filled

    if request.method == "GET" and usrid:
        user_to_prefill = TblUsers.query.filter_by(user_id=usrid).first()
        if user_to_prefill:
            print(f"--- Attempting to pre-fill form for user ID: {usrid} ---")
            # Expected format: "Lastname F."
            name_parts = user_to_prefill.user_name.split(" ", 1)
            form.report_last_name.data = name_parts[0]
            # form.report_first_name.data cannot be accurately prefilled from "F."
            form.email.data = user_to_prefill.user_kontakt
            user_prefilled_data = True
            print(f"Prefilled: Last Name='{form.report_last_name.data}', Email='{form.email.data}'")
        else:
            print(f"--- User ID {usrid} provided for pre-fill, but user not found. ---")

    if request.method == "POST":
        # Rate Limiting Check (before form validation)
        ip_addr = request.remote_addr
        if _check_and_update_ip_submission_count(ip_addr, limit=7):
            print(f"--- Rate limit exceeded for IP: {ip_addr}. Aborting with 429. ---")
            abort(429) # Too Many Requests

        if form.validate_on_submit():
            print(f"--- Form Data Validated (POST) ---")
            # Honeypot Check (after form validation)
            if form.honeypot.data:
                print(f"--- Honeypot triggered by IP: {ip_addr}. Aborting with 403. ---")
                abort(403) # Forbidden
            
            print(f"Form data: {form.data}")
            try:
                # 1. User Handling (Reporter)
                reporter_user_id = get_new_id()
                reporter_name = f"{form.report_last_name.data.strip()} {form.report_first_name.data.strip()[0].upper()}."
                reporter_contact = form.email.data
                reporter = TblUsers(
                    user_id=reporter_user_id,
                    user_name=reporter_name,
                    user_rolle=1,
                    user_kontakt=reporter_contact
                )
                print(f"--- Preparing Reporter User ---")
                print(f"Reporter User ID: {reporter_user_id}")
                print(f"Reporter Name: {reporter_name}")
                print(f"Reporter Contact: {reporter_contact}")
                db.session.add(reporter)
                db.session.flush()

                finder_instance = None
                if not form.identical_finder_reporter.data:
                    if form.finder_first_name.data and form.finder_last_name.data:
                        finder_user_id = get_new_id()
                        finder_name = f"{form.finder_last_name.data.strip()} {form.finder_first_name.data.strip()[0].upper()}."
                        finder_instance = TblUsers(
                            user_id=finder_user_id,
                            user_name=finder_name,
                            user_rolle=2,
                        )
                        print(f"--- Preparing Finder User ---")
                        print(f"Finder User ID: {finder_user_id}")
                        print(f"Finder Name: {finder_name}")
                        db.session.add(finder_instance)
                        db.session.flush()

                # 2. File Upload
                photo_file = form.photo.data
                db_image_path = None
                if photo_file:
                    sighting_date_obj = form.sighting_date.data # Use the date object
                    year_str = sighting_date_obj.strftime("%Y")
                    date_str_for_path = sighting_date_obj.strftime("%Y-%m-%d")
                    upload_dir = Path(Config.UPLOAD_FOLDER) / year_str / date_str_for_path
                    upload_dir.mkdir(parents=True, exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    city_filename_part = secure_filename(form.fund_city.data or "unknown_city")
                    generated_filename = f"{city_filename_part}-{timestamp}-{secure_filename(reporter_user_id)}.webp"
                    full_save_path = upload_dir / generated_filename
                    image_bytes = photo_file.read()
                    photo_file.seek(0)
                    with Image.open(io.BytesIO(image_bytes)) as img:
                        if img.format != 'WEBP' or len(image_bytes) > 6 * 1024 * 1024:
                            output_buffer = io.BytesIO()
                            img.save(output_buffer, format='WEBP', quality=50)
                            image_bytes_to_save = output_buffer.getvalue()
                        else:
                            image_bytes_to_save = image_bytes
                    with open(full_save_path, 'wb') as f:
                        f.write(image_bytes_to_save)
                    db_image_path = str(Path(year_str) / date_str_for_path / generated_filename)

                # 3. Fundort (Location)
                lat = form.latitude.data
                lon = form.longitude.data
                mtb_value = ""
                amt_value = ""
                print(f"--- Processing Location Data ---")
                print(f"Raw Lat/Lon from form: {lat}, {lon}")
                if lat is not None and lon is not None and pointInRect((lat, lon)):
                    mtb_value = get_mtb(lat, lon)
                    amt_value = get_amt_full_scan((lon, lat))
                
                fundort_beschreibung_val = 0
                if form.location_description.data:
                    try:
                        fundort_beschreibung_val = int(form.location_description.data)
                    except (ValueError, TypeError):
                        print(f"Warning: Could not convert location_description '{form.location_description.data}' to int for Fundort.")
                
                new_fundort_data = {
                    'plz': form.fund_zip_code.data or "0", 'ort': form.fund_city.data,
                    'strasse': form.fund_street.data, 'kreis': form.fund_district.data,
                    'land': form.fund_state.data, 'longitude': lon, 'latitude': lat,
                    'mtb': mtb_value, 'amt': amt_value, 'beschreibung': fundort_beschreibung_val,
                    'ablage': db_image_path
                }
                print(f"--- Preparing TblFundorte Data ---")
                print(f"{new_fundort_data=}")
                new_fundort = TblFundorte(**new_fundort_data)
                db.session.add(new_fundort)
                db.session.flush()

                # 4. Meldung (Sighting Report)
                gender_fields_dict = _set_gender_fields(form.gender.data)
                current_time = datetime.now() # Store current time for consistent use
                new_meldung_data = {
                    'dat_fund_von': form.sighting_date.data,
                    'dat_meld': current_time,
                    'fo_zuordnung': new_fundort.id,
                    'fo_quelle': "F", 'art_f': "0", 'tiere': "1",
                    **gender_fields_dict,
                    'anm_melder': form.description.data
                }
                print(f"--- Preparing TblMeldungen Data (fo_zuordnung is now {new_fundort.id}) ---")
                print(f"{new_meldung_data=}")
                new_meldung = TblMeldungen(**new_meldung_data) # Use prepared dict
                db.session.add(new_meldung)
                db.session.flush()

                # 5. MeldungUser (Link User to Sighting)
                meldung_user_link_data = {
                    'id_meldung': new_meldung.id,
                    'id_user': reporter.id
                }
                if finder_instance:
                    meldung_user_link_data['id_finder'] = finder_instance.id
                
                print(f"--- Preparing TblMeldungUser Data (IDs are {new_meldung.id}, {reporter.id}, {finder_instance.id if finder_instance else None}) ---")
                print(f"{meldung_user_link_data=}")
                meldung_user_link = TblMeldungUser(**meldung_user_link_data) # Use prepared dict
                db.session.add(meldung_user_link)

                db.session.commit()

                # Set session flags for success page
                session["report_submission_successful"] = True
                session["last_submission_reporter_id"] = reporter.user_id
                session["submission_had_email"] = bool(reporter.user_kontakt) # True if email was provided
                print(f"--- Report submitted. Session flags set. Reporter ID: {reporter.user_id}, Had Email: {session['submission_had_email']} ---")

                # Instead of redirecting, return a JSON response with the success URL
                success_url = url_for("report.success")
                return jsonify({"success": True, "redirect_url": success_url, "message": "Vielen Dank, Ihre Meldung wurde erfolgreich gespeichert!"}), 200

            except Exception as e:
                db.session.rollback()
                print(f"Error processing new report: {e}")
                flash(
                    "Ein Fehler ist beim Speichern Ihrer Meldung aufgetreten. Bitte versuchen Sie es erneut.",
                    "error",
                )
        else:
            # Form validation failed on POST
            print("--- Form validation failed on POST ---")
            print(f"Form errors: {form.errors}")

    # For GET requests or validation failures, render the form
    # Pass user_prefilled_data to template if you want to conditionally make fields readonly
    return render_template("report/report_form.html", form=form, now=datetime.now, user_prefilled=user_prefilled_data)

@report.route("/success")
def success():
    """Thank you page after successful submission, with session check."""
    print(f"--- Success page accessed. URL: {request.url}, Referrer: {request.referrer} ---")
    
    # Try to get and remove the success flag. If it was present and True, this is the first valid visit.
    was_successful_submission = session.pop("report_submission_successful", False)
    
    last_reporter_id = None
    had_email = False # Default for cases where it's not a fresh submission
    
    if was_successful_submission:
        last_reporter_id = session.pop("last_submission_reporter_id", None)
        had_email = session.pop("submission_had_email", False) # Pop this too
        print(f"--- Success page: Valid first visit. Reporter ID: {last_reporter_id}, Had Email: {had_email} ---")
    else:
        # This means the flag was not present (e.g., refresh, direct access)
        print(f"--- Success page: Accessed via refresh, direct link, or after flag was cleared. ---")
        # If accessed directly or refreshed, had_email will be False, so the general message will be shown.
        # last_reporter_id will remain None, making links generic.

    # The template will render. If last_reporter_id is None, the links
    # /melden/{{usrid}} will become /melden/
    # /sichtungen/{{usrid}} will become /sichtungen/
    # These base URLs should lead to appropriate general pages.
    # Pass 'addresse' as a string 'True'/'False' for the template's conditional logic.
    return render_template("report/success-new.html", usrid=last_reporter_id, addresse=str(had_email))


# Helper function to get fields relevant to a step
def get_step_fields(step):
    """Return a list of field names relevant to a specific form step"""
    step_fields_map = {
        1: ['gender', 'location_description', 'description'],  # Photo is handled client-side for validation step
        2: ['sighting_date', 'latitude', 'longitude', 'fund_city', 'fund_state', 'fund_zip_code', 'fund_district', 'fund_street'],
        3: ['report_first_name', 'report_last_name', 'email', 'identical_finder_reporter', 'finder_first_name', 'finder_last_name'], # Moved contact fields here
        4: [], # Review step doesn't need AJAX validation of specific fields before submit
    }
    return step_fields_map.get(step, [])

@report.route("/validate_step", methods=["POST"])
def validate_step():
    """Validate a single step of the form via AJAX using WTForms."""
    # Get JSON data from request
    data = request.json
    step = data.get("step", 1)
    
    # Get relevant fields for the current step
    step_fields = get_step_fields(step)
    if not step_fields:
        # Step 3 (empty) or Review step, considered valid for navigation purposes
        return jsonify({"valid": True, "errors": {}})
    
    # Create a MultiDict for WTForms, handling boolean checkbox correctly
    form_data = MultiDict(data)
    if 'identical_finder_reporter' in data:
        form_data['identical_finder_reporter'] = data['identical_finder_reporter'] == 'true' or data['identical_finder_reporter'] is True
    
    # Create form instance with the data
    form = MantisSightingForm(formdata=form_data, csrf_enabled=False)  # Disable CSRF for AJAX validation
    
    is_valid = True
    errors = {}
    
    # Validate only the fields relevant to this step
    for field_name in step_fields:
        field = getattr(form, field_name, None)
        if field:
            # Validate this specific field using the form context
            if not field.validate(form): # This runs standard validators (DataRequired, Length, etc.)
                is_valid = False
                errors[field_name] = field.errors

    # If field-level validation passed AND it's Step 3, run the custom cross-field check
    if is_valid and step == 3:
        if not form.validate_finder_names_dependency(): # Call our specific cross-field validator
            is_valid = False
            # Manually add errors from the custom validation if any
            if 'finder_first_name' in form.errors:
                errors['finder_first_name'] = form.errors['finder_first_name']
            if 'finder_last_name' in form.errors:
                errors['finder_last_name'] = form.errors['finder_last_name']

    # Special case for step 2: Validate coordinates (keep this logic, apply only if field validation passed)
    if is_valid and step == 2:
        lat = data.get("latitude", "")
        lng = data.get("longitude", "")
        
        if not lat or not lng:
            is_valid = False
            errors["coordinates"] = ["Bitte wählen Sie einen Standort auf der Karte"]
        else:
            try:
                lat_float = float(lat)
                lng_float = float(lng)
                
                # Range check for valid coordinates
                if not (-90 <= lat_float <= 90) or not (-180 <= lng_float <= 180):
                    is_valid = False
                    errors["coordinates"] = ["Ungültige Koordinaten. Bitte wählen Sie einen gültigen Standort."]
            except ValueError:
                is_valid = False
                errors["coordinates"] = ["Ungültiges Koordinatenformat"]
    
    return jsonify({"valid": is_valid, "errors": errors})