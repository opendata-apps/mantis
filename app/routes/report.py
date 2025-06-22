import io
from datetime import datetime
from pathlib import Path

from flask import (
    Blueprint,
    flash,
    jsonify,
    render_template,
    request,
    url_for,
    abort,
    session
)
from werkzeug.datastructures import MultiDict
from werkzeug.utils import secure_filename
from PIL import Image

from app import db, limiter, csrf
from app.database.models import (
    TblFundorte,
    TblMeldungen,
    TblMeldungUser,
    TblUsers,
    TblUserFeedback
)
from app.forms import MantisSightingForm
from app.tools.gen_user_id import get_new_id
from app.tools.mtb_calc import get_mtb, pointInRect
from app.tools.gemeinde_finder import get_amt_full_scan
from ..config import Config

# Blueprints
report = Blueprint("report", __name__)

# Helper function to determine gender fields for TblMeldungen
def _set_gender_fields(selected_gender_value):
    """Maps gender string to TblMeldungen database fields."""
    gender_mapping = {
        "Männlich": "art_m",
        "Weiblich": "art_w", 
        "Nymphe": "art_n",
        "Oothek": "art_o",
        "Unbekannt": "art_f"
    }
    
    genders = {"art_m": 0, "art_w": 0, "art_n": 0, "art_o": 0, "art_f": 0}
    field_name = gender_mapping.get(selected_gender_value)
    if field_name:
        genders[field_name] = 1
    return genders

def _process_uploaded_image(photo_file, sighting_date, city_name, user_id):
    """Process uploaded image - trust client-optimized WebP files to avoid double compression."""
    year_str = sighting_date.strftime("%Y")
    date_str = sighting_date.strftime("%Y-%m-%d")
    upload_dir = Path(Config.UPLOAD_FOLDER) / year_str / date_str
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    city_part = secure_filename(city_name or "unknown_city")
    filename = f"{city_part}-{timestamp}-{secure_filename(user_id)}.webp"
    full_path = upload_dir / filename
    
    image_bytes = photo_file.read()
    photo_file.seek(0)
    
    with Image.open(io.BytesIO(image_bytes)) as img:
        file_size_mb = len(image_bytes) / (1024 * 1024)
        
        if img.format == 'WEBP' and file_size_mb <= 8.0:
            # Trust client-optimized WebP
            image_bytes_to_save = image_bytes
        else:
            # Re-compress if needed
            output_buffer = io.BytesIO()
            img.save(output_buffer, format='WEBP', quality=60)
            image_bytes_to_save = output_buffer.getvalue()
    
    with open(full_path, 'wb') as f:
        f.write(image_bytes_to_save)
    
    return str(Path(year_str) / date_str / filename)

def _create_user(first_name, last_name, email, role=1):
    """Create a new user with standardized name format."""
    user_id = get_new_id()
    name = f"{last_name.strip()} {first_name.strip()[0].upper()}."
    return TblUsers(
        user_id=user_id,
        user_name=name,
        user_rolle=role,
        user_kontakt=email
    )

def _parse_user_name(user_name):
    """Parse database user_name format 'Lastname F.' into components."""
    name_parts = user_name.split(" ", 1)
    last_name = name_parts[0]
    
    if len(name_parts) >= 2:
        initial_part = name_parts[1].strip()
        if initial_part.endswith(".") and len(initial_part) == 2:
            first_name = initial_part[0]
        else:
            first_name = initial_part
    else:
        first_name = name_parts[0][0] if name_parts[0] else "X"
    
    return last_name, first_name

@report.route("/melden", methods=["GET", "POST"])
@report.route("/melden/<usrid>", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
@limiter.limit("3 per minute", methods=["POST"])
def melden(usrid=None):
    """Handle mantis sighting report form submission with user prefilling support."""
    form = MantisSightingForm()
    user_prefilled_data = False
    user_has_feedback = False

    # Handle GET request with user prefilling
    if request.method == "GET" and usrid:
        user_to_prefill = TblUsers.query.filter_by(user_id=usrid).first()
        if user_to_prefill:
            last_name, first_name = _parse_user_name(user_to_prefill.user_name)
            
            form.report_last_name.data = last_name
            form.report_first_name.data = first_name
            form.email.data = user_to_prefill.user_kontakt or ""
            
            # Check if user already provided feedback
            user_has_feedback = TblUserFeedback.query.filter_by(user_id=user_to_prefill.id).first() is not None
            user_prefilled_data = True

    if request.method == "POST":
        if form.validate_on_submit():
            # Security: Check honeypot field
            if form.honeypot.data:
                abort(403)
            
            try:
                # 1. Handle reporter user (existing or new)
                if usrid:
                    reporter = TblUsers.query.filter_by(user_id=usrid).first()
                    if not reporter:
                        # User ID provided but not found, create new user
                        reporter = _create_user(
                            form.report_first_name.data,
                            form.report_last_name.data,
                            form.email.data
                        )
                        db.session.add(reporter)
                        db.session.flush()
                else:
                    # No user ID provided, create new user
                    reporter = _create_user(
                        form.report_first_name.data,
                        form.report_last_name.data,
                        form.email.data
                    )
                    db.session.add(reporter)
                    db.session.flush()

                # 2. Handle finder user (if different from reporter)
                finder_instance = None
                if not form.identical_finder_reporter.data:
                    if form.finder_first_name.data and form.finder_last_name.data:
                        finder_instance = _create_user(
                            form.finder_first_name.data,
                            form.finder_last_name.data,
                            "",
                            role=2
                        )
                        db.session.add(finder_instance)
                        db.session.flush()

                # 3. Handle user feedback (how did you hear about us?)
                if form.feedback_source.data:
                    try:
                        feedback_type_id = int(form.feedback_source.data)
                        existing_feedback = TblUserFeedback.query.filter_by(user_id=reporter.id).first()
                        
                        if not existing_feedback:
                            user_feedback = TblUserFeedback(
                                user_id=reporter.id,
                                feedback_type_id=feedback_type_id,
                                source_detail=form.feedback_detail.data
                            )
                            db.session.add(user_feedback)
                    except (ValueError, TypeError):
                        pass  # Invalid feedback data, skip silently

                # 4. Process uploaded photo
                db_image_path = None
                if form.photo.data:
                    db_image_path = _process_uploaded_image(
                        form.photo.data, 
                        form.sighting_date.data, 
                        form.fund_city.data, 
                        reporter.user_id
                    )

                # 5. Create location record
                lat, lon = form.latitude.data, form.longitude.data
                mtb_value = amt_value = ""
                
                if lat is not None and lon is not None and pointInRect((lat, lon)):
                    mtb_value = get_mtb(lat, lon)
                    amt_value = get_amt_full_scan((lon, lat))
                
                location_description = 0
                if form.location_description.data:
                    try:
                        location_description = int(form.location_description.data)
                    except (ValueError, TypeError):
                        pass
                
                fundort = TblFundorte(
                    plz=form.fund_zip_code.data or "0",
                    ort=form.fund_city.data,
                    strasse=form.fund_street.data,
                    kreis=form.fund_district.data,
                    land=form.fund_state.data,
                    longitude=lon,
                    latitude=lat,
                    mtb=mtb_value,
                    amt=amt_value,
                    beschreibung=location_description,
                    ablage=db_image_path
                )
                db.session.add(fundort)
                db.session.flush()

                # 6. Create sighting record
                gender_fields = _set_gender_fields(form.gender.data)
                meldung = TblMeldungen(
                    dat_fund_von=form.sighting_date.data,
                    dat_meld=datetime.now(),
                    fo_zuordnung=fundort.id,
                    fo_quelle="F",
                    tiere="1",
                    anm_melder=form.description.data,
                    **gender_fields
                )
                db.session.add(meldung)
                db.session.flush()

                # 7. Link user to sighting
                user_link = TblMeldungUser(
                    id_meldung=meldung.id,
                    id_user=reporter.id,
                    id_finder=finder_instance.id if finder_instance else None
                )
                db.session.add(user_link)
                db.session.commit()

                # Set session data for success page
                session["report_submission_successful"] = True
                session["last_submission_reporter_id"] = reporter.user_id
                session["submission_had_email"] = bool(reporter.user_kontakt)

                return jsonify({
                    "success": True, 
                    "redirect_url": url_for("report.success"),
                    "message": "Vielen Dank, Ihre Meldung wurde erfolgreich gespeichert!"
                }), 200

            except Exception:
                db.session.rollback()
                flash("Ein Fehler ist beim Speichern Ihrer Meldung aufgetreten. Bitte versuchen Sie es erneut.", "error")
        
    return render_template(
        "report/report_form.html", 
        form=form, 
        now=datetime.now, 
        user_prefilled=user_prefilled_data, 
        user_has_feedback=user_has_feedback
    )

@report.route("/success")
def success():
    """Display success page after form submission with session validation."""
    was_successful_submission = session.pop("report_submission_successful", False)
    
    if was_successful_submission:
        last_reporter_id = session.pop("last_submission_reporter_id", None)
        had_email = session.pop("submission_had_email", False)
    else:
        last_reporter_id = None
        had_email = False

    return render_template(
        "report/success-new.html", 
        usrid=last_reporter_id, 
        addresse=str(had_email)
    )

def get_step_fields(step):
    """Return field names for form step validation."""
    step_fields = {
        1: ['gender', 'location_description', 'description'],
        2: ['sighting_date', 'latitude', 'longitude', 'fund_city', 'fund_state', 'fund_zip_code', 'fund_district', 'fund_street'],
        3: ['report_first_name', 'report_last_name', 'email', 'identical_finder_reporter', 'finder_first_name', 'finder_last_name', 'feedback_source', 'feedback_detail'],
        4: []  # Review step has no specific field validation
    }
    return step_fields.get(step, [])

@report.route("/validate_step", methods=["POST"])
@csrf.exempt
@limiter.limit("30 per minute")
def validate_step():
    """Validate form step via AJAX."""
    data = request.json
    step = data.get("step", 1)
    step_fields = get_step_fields(step)
    
    if not step_fields:
        return jsonify({"valid": True, "errors": {}})
    
    # Prepare form data for validation
    form_data = MultiDict(data)
    if 'identical_finder_reporter' in data:
        form_data['identical_finder_reporter'] = data['identical_finder_reporter'] in ('true', True)
    
    form = MantisSightingForm(formdata=form_data, csrf_enabled=False)
    
    is_valid = True
    errors = {}
    
    # Validate step-specific fields
    for field_name in step_fields:
        field = getattr(form, field_name, None)
        if field and not field.validate(form):
            is_valid = False
            errors[field_name] = field.errors

    # Step 3: Cross-field validation for finder names
    if is_valid and step == 3:
        if not form.validate_finder_names_dependency():
            is_valid = False
            if 'finder_first_name' in form.errors:
                errors['finder_first_name'] = form.errors['finder_first_name']
            if 'finder_last_name' in form.errors:
                errors['finder_last_name'] = form.errors['finder_last_name']

    # Step 2: Coordinate validation
    if is_valid and step == 2:
        lat = data.get("latitude", "")
        lng = data.get("longitude", "")
        
        if not lat or not lng:
            is_valid = False
            errors["coordinates"] = ["Bitte wählen Sie einen Standort auf der Karte"]
        else:
            try:
                lat_float, lng_float = float(lat), float(lng)
                if not (-90 <= lat_float <= 90) or not (-180 <= lng_float <= 180):
                    is_valid = False
                    errors["coordinates"] = ["Ungültige Koordinaten. Bitte wählen Sie einen gültigen Standort."]
            except ValueError:
                is_valid = False
                errors["coordinates"] = ["Ungültiges Koordinatenformat"]
    
    return jsonify({"valid": is_valid, "errors": errors})