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
    session,
    current_app,
)
from werkzeug.datastructures import MultiDict
from werkzeug.utils import secure_filename
from PIL import Image

from app import db, limiter
from sqlalchemy import select
from app.database.models import (
    TblFundorte,
    TblMeldungen,
    TblMeldungUser,
    TblUsers,
    TblUserFeedback,
)
from app.database.feedback_type import FeedbackSource
from app.forms import MantisSightingForm
from app.tools.gen_user_id import get_new_id
from app.tools.mtb_calc import get_mtb, pointInRect
from app.tools.gemeinde_finder import get_amt_full_scan

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
        # "Unbekannt" is no longer mapped to art_f
    }

    genders = {"art_m": 0, "art_w": 0, "art_n": 0, "art_o": 0, "art_f": 0}
    field_name = gender_mapping.get(selected_gender_value)
    if field_name:
        genders[field_name] = 1
    # For "Unbekannt" or empty selection, all fields remain 0
    return genders


def _process_uploaded_image(photo_file, sighting_date, city_name, user_id):
    """Process uploaded image - trust client-optimized WebP files to avoid double compression."""
    year_str = sighting_date.strftime("%Y")
    date_str = sighting_date.strftime("%Y-%m-%d")
    upload_dir = Path(current_app.config["UPLOAD_FOLDER"]) / year_str / date_str
    upload_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    city_part = secure_filename(city_name or "unknown_city")
    filename = f"{city_part}-{timestamp}-{secure_filename(user_id)}.webp"
    full_path = upload_dir / filename

    image_bytes = photo_file.read()
    photo_file.seek(0)

    with Image.open(io.BytesIO(image_bytes)) as img:
        file_size_mb = len(image_bytes) / (1024 * 1024)

        if img.format == "WEBP" and file_size_mb <= 8.0:
            # Trust client-optimized WebP
            image_bytes_to_save = image_bytes
        else:
            # Re-compress if needed
            output_buffer = io.BytesIO()
            img.save(output_buffer, format="WEBP", quality=60)
            image_bytes_to_save = output_buffer.getvalue()

    with open(full_path, "wb") as f:
        f.write(image_bytes_to_save)

    return str(Path(year_str) / date_str / filename)


def _create_user(first_name, last_name, email, role=1):
    """Create a new user with standardized name format."""
    user_id = get_new_id()
    name = f"{last_name.strip()} {first_name.strip()[0].upper()}."
    user = TblUsers()
    user.user_id = user_id
    user.user_name = name
    user.user_rolle = role
    user.user_kontakt = email
    return user


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
        user_to_prefill = db.session.scalar(
            select(TblUsers).where(TblUsers.user_id == usrid)
        )
        if user_to_prefill:
            last_name, first_name = _parse_user_name(user_to_prefill.user_name)

            form.report_last_name.data = last_name
            form.report_first_name.data = first_name
            form.email.data = user_to_prefill.user_kontakt or ""

            # Check if user already provided feedback
            user_has_feedback = user_to_prefill.feedback_source is not None
            user_prefilled_data = True

    if request.method == "POST":
        if form.validate_on_submit():
            # Security: Check honeypot field
            if form.honeypot.data:
                abort(403)

            try:
                # 1. Handle reporter user (existing or new)
                if usrid:
                    reporter = db.session.scalar(
                        select(TblUsers).where(TblUsers.user_id == usrid)
                    )
                    if not reporter:
                        # User ID provided but not found, create new user
                        reporter = _create_user(
                            form.report_first_name.data,
                            form.report_last_name.data,
                            form.email.data,
                        )
                        db.session.add(reporter)
                        db.session.flush()
                else:
                    # No user ID provided, create new user
                    reporter = _create_user(
                        form.report_first_name.data,
                        form.report_last_name.data,
                        form.email.data,
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
                            role=2,
                        )
                        db.session.add(finder_instance)
                        db.session.flush()

                # 3. Handle user feedback (how did you hear about us?)
                if form.feedback_source.data and not reporter.feedback_source:
                    user_feedback = TblUserFeedback()
                    user_feedback.user_id = reporter.id
                    user_feedback.feedback_source = form.feedback_source.data
                    user_feedback.source_detail = form.feedback_detail.data
                    db.session.add(user_feedback)

                # 4. Process uploaded photo
                db_image_path = None
                if form.photo.data:
                    db_image_path = _process_uploaded_image(
                        form.photo.data,
                        form.sighting_date.data,
                        form.fund_city.data,
                        reporter.user_id,
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

                fundort = TblFundorte()
                fundort.plz = form.fund_zip_code.data or "0"
                fundort.ort = form.fund_city.data
                fundort.strasse = form.fund_street.data
                fundort.kreis = form.fund_district.data
                fundort.land = form.fund_state.data
                fundort.longitude = lon
                fundort.latitude = lat
                fundort.mtb = mtb_value
                fundort.amt = amt_value
                fundort.beschreibung = location_description
                fundort.ablage = db_image_path
                db.session.add(fundort)
                db.session.flush()

                # 6. Create sighting record
                gender_fields = _set_gender_fields(form.gender.data)
                meldung = TblMeldungen()
                meldung.dat_fund_von = form.sighting_date.data
                meldung.dat_meld = datetime.now()
                meldung.fo_zuordnung = fundort.id
                meldung.fo_quelle = "F"
                meldung.tiere = "1"
                meldung.anm_melder = form.description.data

                # Set gender fields
                for field, value in gender_fields.items():
                    setattr(meldung, field, value)
                db.session.add(meldung)
                db.session.flush()

                # 7. Link user to sighting
                user_link = TblMeldungUser()
                user_link.id_meldung = meldung.id
                user_link.id_user = reporter.id
                user_link.id_finder = finder_instance.id if finder_instance else None
                db.session.add(user_link)
                db.session.commit()

                # Set session data for success page
                session["report_submission_successful"] = True
                session["last_submission_reporter_id"] = reporter.user_id
                session["submission_had_email"] = bool(reporter.user_kontakt)

                return jsonify(
                    {
                        "success": True,
                        "redirect_url": url_for("report.success"),
                        "message": "Vielen Dank, Ihre Meldung wurde erfolgreich gespeichert!",
                    }
                ), 200

            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Failed to save report: {str(e)}")
                flash(
                    "Ein Fehler ist beim Speichern Ihrer Meldung aufgetreten. Bitte versuchen Sie es erneut.",
                    "error",
                )

    return render_template(
        "report/report_form.html",
        form=form,
        now=datetime.now,
        user_prefilled=user_prefilled_data,
        user_has_feedback=user_has_feedback,
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
        "report/success-new.html", usrid=last_reporter_id, addresse=str(had_email)
    )


def get_step_fields(step):
    """Return field names for form step validation."""
    step_fields = {
        1: ["gender", "location_description", "description"],
        2: [
            "sighting_date",
            "latitude",
            "longitude",
            "fund_city",
            "fund_state",
            "fund_zip_code",
            "fund_district",
            "fund_street",
        ],
        3: [
            "report_first_name",
            "report_last_name",
            "email",
            "identical_finder_reporter",
            "finder_first_name",
            "finder_last_name",
            "feedback_source",
            "feedback_detail",
        ],
        4: [],  # Review step has no specific field validation
    }
    return step_fields.get(step, [])


def get_visible_error_fields(step):
    """Return field names that have visible error containers (for OOB clearing).

    Note: Only includes fields rendered via render_form_field macro (which creates error divs).
    Excludes: latitude/longitude (use 'coordinates'), finder fields (no error containers),
              feedback_source/feedback_detail (rendered manually without error containers).
    """
    visible_fields = {
        1: ["photo", "gender", "location_description", "description"],
        2: [
            "sighting_date",
            "fund_city",
            "fund_state",
            "fund_zip_code",
            "fund_district",
            "fund_street",
        ],
        3: ["report_first_name", "report_last_name", "email"],
        4: [],
    }
    return visible_fields.get(step, [])


# ============================================================================
# HTMX Routes for Form Interactions
# ============================================================================


def _is_partial_request():
    """Check if the current request is an HTMX request."""
    return request.headers.get("HX-Request") == "true"


@report.route("/melden/validate-step", methods=["POST"])
@limiter.limit("60 per minute")
def validate_step_partial():
    """HTMX endpoint for step validation - returns HTML partial with errors or success indicator."""
    if not _is_partial_request():
        abort(400)

    # Parse step strictly: malformed values must not silently fall back to step 1.
    step_raw = request.form.get("step", "1")
    try:
        step = int(str(step_raw).strip())
    except (TypeError, ValueError):
        step = None

    if step not in {1, 2, 3, 4}:
        return (
            render_template(
                "report/partials/_validation_errors.html",
                errors={"step": ["Ungültiger Formularschritt."]},
            ),
            400,
        )
    step_fields = get_step_fields(step)

    # Build form data from request
    form_data = MultiDict(request.form)
    if "identical_finder_reporter" in request.form:
        form_data["identical_finder_reporter"] = request.form.get(
            "identical_finder_reporter"
        ) in ("true", "on", "1", "True")

    form = MantisSightingForm(formdata=form_data, meta={"csrf": False})

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
            if form.finder_first_name.errors:
                errors["finder_first_name"] = form.finder_first_name.errors
            if form.finder_last_name.errors:
                errors["finder_last_name"] = form.finder_last_name.errors

    if is_valid:
        # Return a trigger to advance to next step + clear any previous errors via OOB
        from flask import make_response

        visible_fields = get_visible_error_fields(step)
        clear_html = render_template(
            "report/partials/_clear_errors.html", fields=visible_fields, step=step
        )
        response = make_response(clear_html)
        response.headers["HX-Trigger"] = (
            f'{{"stepValid": {{"step": {step}, "nextStep": {step + 1}}}}}'
        )
        return response
    else:
        # Return inline error messages via OOB swaps
        return render_template("report/partials/_validation_errors.html", errors=errors)


@report.route("/melden/toggle-finder", methods=["POST"])
def toggle_finder():
    """HTMX endpoint to toggle finder fields visibility."""
    if not _is_partial_request():
        abort(400)

    is_identical = request.form.get("identical_finder_reporter") in (
        "true",
        "on",
        "1",
        "True",
    )

    if is_identical:
        # Return hidden/empty finder fields
        return render_template("report/partials/_finder_fields.html", show=False)
    else:
        # Return visible finder fields
        form = MantisSightingForm()
        return render_template(
            "report/partials/_finder_fields.html", show=True, form=form
        )


@report.route("/melden/feedback-detail", methods=["POST"])
def feedback_detail():
    """HTMX endpoint to show/hide feedback detail field based on selection."""
    if not _is_partial_request():
        abort(400)

    feedback_source = request.form.get("feedback_source", "")

    if feedback_source:
        placeholder = FeedbackSource.get_placeholder(feedback_source)
        if placeholder:
            return render_template(
                "report/partials/_feedback_detail.html",
                show=True,
                placeholder=placeholder,
            )
    return render_template("report/partials/_feedback_detail.html", show=False)


@report.route("/melden/review", methods=["POST"])
@limiter.limit("30 per minute")
def review_step():
    """HTMX endpoint to generate the review section content from form data."""
    if not _is_partial_request():
        abort(400)

    # Collect all form data for the review
    review_data = {
        # Step 1: Photo & Details
        "gender": _get_gender_display(request.form.get("gender", "")),
        "location_description": _get_location_description_display(
            request.form.get("location_description", "")
        ),
        "description": request.form.get("description", "-") or "-",
        # photo_data injected client-side via htmx:afterSwap to avoid ~4MB round-trip
        "photo_data": "",
        # Step 2: Location & Date
        "sighting_date": _format_date(request.form.get("sighting_date", "")),
        "latitude": request.form.get("latitude", ""),
        "longitude": request.form.get("longitude", ""),
        "coordinates": _format_coordinates(
            request.form.get("latitude", ""), request.form.get("longitude", "")
        ),
        "fund_city": request.form.get("fund_city", "-") or "-",
        "fund_state": request.form.get("fund_state", "-") or "-",
        "fund_district": request.form.get("fund_district", "-") or "-",
        "fund_street": request.form.get("fund_street", "-") or "-",
        "fund_zip_code": request.form.get("fund_zip_code", "-") or "-",
        # Step 3: Contact
        "reporter_name": f"{request.form.get('report_first_name', '')} {request.form.get('report_last_name', '')}".strip()
        or "-",
        "email": request.form.get("email", "-") or "-",
        "identical_finder": request.form.get("identical_finder_reporter")
        in ("true", "on", "1", "True"),
        "finder_name": _get_finder_name(request.form),
        "feedback_source": _get_feedback_source_display(
            request.form.get("feedback_source", "")
        ),
        "feedback_detail": request.form.get("feedback_detail", ""),
    }

    return render_template("report/partials/_review_content.html", review=review_data)


@report.route("/melden/char-count", methods=["POST"])
def char_count():
    """HTMX endpoint to update character count display."""
    if not _is_partial_request():
        abort(400)

    description = request.form.get("description", "")
    max_length = 500
    remaining = max_length - len(description)
    is_over = remaining < 0

    return render_template(
        "report/partials/_char_count.html", remaining=remaining, is_over=is_over
    )


# Helper functions for review display
def _get_gender_display(gender_value):
    """Convert gender field value to display text."""
    from app.forms import GENDER_CHOICES

    for value, label in GENDER_CHOICES:
        if value == gender_value:
            return label
    return "-"


def _get_location_description_display(location_value):
    """Convert location description value to display text."""
    from app.forms import LOCATION_DESCRIPTION_CHOICES

    for value, label in LOCATION_DESCRIPTION_CHOICES:
        if value == location_value:
            return label
    return "-"


def _get_feedback_source_display(feedback_value):
    """Convert feedback source value to display text."""
    if not feedback_value:
        return "Nicht angegeben"
    return FeedbackSource.get_display_name(feedback_value)


def _format_date(date_str):
    """Format date string for display."""
    if not date_str:
        return "-"
    try:
        from datetime import datetime

        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%d.%m.%Y")
    except ValueError:
        return date_str


def _format_coordinates(lat, lng):
    """Format coordinates for display."""
    if lat and lng:
        try:
            return f"{float(lat):.6f}, {float(lng):.6f}"
        except ValueError:
            pass
    return "-"


def _get_finder_name(form_data):
    """Get finder name from form data."""
    first = form_data.get("finder_first_name", "")
    last = form_data.get("finder_last_name", "")
    name = f"{first} {last}".strip()
    return name if name else "-"
