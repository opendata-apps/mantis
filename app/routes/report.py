import io
import json
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote, urlencode

from flask import (
    Blueprint,
    jsonify,
    make_response,
    render_template,
    request,
    url_for,
    abort,
    session,
    current_app,
)
from werkzeug.datastructures import MultiDict
from PIL import Image, ImageOps

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
from app.tools.mtb_calc import point_in_rect
from app.tools.gemeinde_finder import get_amt_enriched
from app.tools.location_enrichment import calculate_spatial_fields
from app.tools.report_images import build_upload_filename, ensure_upload_dir

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


# Matches the client's own downscale target, so a photo is archived at the same
# size whether the browser converted it or the server did.
MAX_STORED_DIMENSION = 2048


class BlankImageError(ValueError):
    """The uploaded frame has no visible pixels."""


def _validation_error_response(errors):
    """Field-level rejection in the shape `showServerErrors` expects."""
    return jsonify(
        {"success": False, "error": "Ungültige Formulardaten.", "errors": errors}
    ), 400


def _has_no_visible_pixels(img):
    """True when every pixel is fully transparent.

    An Android WebView can drop ``drawImage`` without raising, and the canvas is
    then encoded at full size still holding its initial value — transparent
    black. Such a frame is worthless to a reviewer but looks like a valid image
    file, so it has to be caught by content rather than by byte size (report
    21953 was 22KB, twice the client-side size threshold).
    """
    if not img.has_transparency_data:
        return False
    # RGBA/LA already carry alpha as a band; only palette transparency needs a
    # convert to read it.
    alpha = (
        img.getchannel("A")
        if img.mode in ("RGBA", "LA")
        else img.convert("RGBA").getchannel("A")
    )
    return alpha.getextrema() == (0, 0)


def _process_uploaded_image(photo_file, sighting_date, city_name, user_id):
    """Process uploaded image - trust client-optimized WebP files to avoid double compression."""
    upload_root = Path(current_app.config["UPLOAD_FOLDER"])
    upload_dir = ensure_upload_dir(upload_root, sighting_date)
    filename = build_upload_filename(city_name, user_id, datetime.now())
    full_path = upload_dir / filename

    image_bytes = photo_file.read()
    photo_file.seek(0)

    with Image.open(io.BytesIO(image_bytes)) as img:
        if _has_no_visible_pixels(img):
            raise BlankImageError("uploaded frame has no visible pixels")

        file_size_mb = len(image_bytes) / (1024 * 1024)

        if img.format == "WEBP" and file_size_mb <= 8.0:
            # Trust client-optimized WebP
            image_bytes_to_save = image_bytes
        else:
            # A browser bakes EXIF orientation into the canvas, but an original
            # uploaded by the conversion fallback arrives untouched and the WebP
            # re-encode drops the tag — so rotate here or a portrait photo is
            # archived sideways with nothing left to fix it.
            output_buffer = io.BytesIO()
            ImageOps.exif_transpose(img, in_place=True)
            # The client caps its own output at 2048; an original forwarded by
            # the conversion fallback has had no such cap, and a 12MP frame
            # re-encodes to ~0.9MB against the ~0.16MB the converted path
            # produces. Cap here so the archive is uniform either way.
            img.thumbnail((MAX_STORED_DIMENSION, MAX_STORED_DIMENSION))
            img.save(output_buffer, format="WEBP", quality=60)
            image_bytes_to_save = output_buffer.getvalue()

    with open(full_path, "wb") as f:
        f.write(image_bytes_to_save)

    return str((upload_dir / filename).relative_to(upload_root))


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
            user_has_feedback = user_to_prefill.feedback_source is not None
            user_prefilled_data = True

    if request.method == "POST":
        if form.validate_on_submit():
            # Security: Check honeypot field
            if form.honeypot.data:
                abort(403)

            try:
                reporter = (
                    db.session.scalar(select(TblUsers).where(TblUsers.user_id == usrid))
                    if usrid
                    else None
                )
                if not reporter:
                    reporter = _create_user(
                        form.report_first_name.data,
                        form.report_last_name.data,
                        form.email.data,
                    )
                    db.session.add(reporter)
                    db.session.flush()

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

                if form.feedback_source.data and not reporter.feedback_source:
                    user_feedback = TblUserFeedback()
                    user_feedback.user_id = reporter.id
                    user_feedback.feedback_source = form.feedback_source.data
                    user_feedback.source_detail = form.feedback_detail.data
                    db.session.add(user_feedback)

                db_image_path = None
                if form.photo.data:
                    db_image_path = _process_uploaded_image(
                        form.photo.data,
                        form.sighting_date.data,
                        form.fund_city.data,
                        reporter.user_id,
                    )

                lat, lon = form.latitude.data, form.longitude.data
                spatial_fields = calculate_spatial_fields(lat, lon)

                location_description_data = form.location_description.data
                if not isinstance(location_description_data, str):
                    raise RuntimeError(
                        "Expected location description after successful form validation"
                    )
                location_description = int(location_description_data)

                fundort = TblFundorte()
                fundort.plz = form.fund_zip_code.data or "0"
                fundort.ort = form.fund_city.data
                fundort.strasse = form.fund_street.data
                # AGS spatial data is authoritative for land/kreis;
                # fall back to Nominatim (form) only if spatial lookup missed
                fundort.kreis = spatial_fields["kreis"] or form.fund_district.data
                fundort.land = spatial_fields["land"] or form.fund_state.data
                fundort.longitude = lon
                fundort.latitude = lat
                fundort.mtb = spatial_fields["mtb"]
                fundort.amt = spatial_fields["amt"]
                fundort.beschreibung = location_description
                fundort.ablage = db_image_path
                db.session.add(fundort)
                db.session.flush()

                gender_fields = _set_gender_fields(form.gender.data)
                meldung = TblMeldungen()
                meldung.dat_fund_von = form.sighting_date.data
                meldung.dat_meld = datetime.now()
                meldung.fo_zuordnung = fundort.id
                meldung.fo_quelle = "F"
                meldung.tiere = "1"
                meldung.anm_melder = form.description.data

                for field, value in gender_fields.items():
                    setattr(meldung, field, value)
                db.session.add(meldung)
                db.session.flush()

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

            except BlankImageError:
                # The check runs before anything is written, so only the
                # transaction needs unwinding. Reported as a field error so the
                # reporter re-picks the photo and keeps the rest of the form.
                db.session.rollback()
                # Same shape as the client beacon, so one grep over
                # "Photo pipeline failed" finds every instance of this bug.
                current_app.logger.warning(
                    "Photo pipeline failed: stage=%s error=%s size=%s type=%s ext=%s ua=%s",
                    "blank-canvas",
                    "rejected at upload",
                    None,
                    None,
                    None,
                    request.user_agent.string[:200],
                )
                return _validation_error_response(
                    {
                        "photo": [
                            "Das Foto enthält kein sichtbares Bild. "
                            "Bitte wählen Sie es erneut aus."
                        ]
                    }
                )

            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Failed to save report: {str(e)}")
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Ein Fehler ist beim Speichern Ihrer Meldung aufgetreten.",
                        }
                    ),
                    500,
                )
        else:
            return _validation_error_response(form.errors)

    response = make_response(
        render_template(
            "report/report_form.html",
            form=form,
            now=datetime.now,
            timedelta=timedelta,
            user_prefilled=user_prefilled_data,
            user_has_feedback=user_has_feedback,
        )
    )
    if user_prefilled_data:
        # A prefilled form embeds the reporter's name + email in the markup;
        # keep it out of search and AI indexes. Pairs with the meta-robots tag
        # in report_form.html (page-level noindex, not a robots.txt Disallow —
        # a disallowed page can't be crawled to read the noindex).
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response


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


def _is_checkbox_true(value):
    """Check if a form checkbox value is truthy."""
    return value in ("true", "on", "1", "True")


@report.route("/melden/ags-lookup")
@limiter.limit("30 per minute")
def ags_lookup():
    """Return AGS spatial data for given coordinates.

    Called by the report form JS to fill land/kreis fields from authoritative
    BKG data instead of relying solely on Nominatim.
    """
    try:
        lat = float(request.args["lat"])
        lon = float(request.args["lon"])
    except (KeyError, ValueError, TypeError):
        return jsonify({}), 400

    if not (30 <= lat <= 60 and -20 <= lon <= 30):
        return jsonify({}), 400

    if not point_in_rect((lat, lon)):
        return jsonify({})

    spatial = get_amt_enriched((lon, lat))
    if not spatial:
        return jsonify({})

    return jsonify(
        {
            "land": spatial["land"],
            "kreis": spatial["kreis"],
        }
    )


def _beacon_field(value, limit):
    """Everything in the beacon is client-supplied and lands in a log line, so
    collapse whitespace — a newline in there would forge a second entry."""
    return " ".join(str(value).split())[:limit]


# Checked in order, so the more specific token wins: an iPad UA also contains
# "Macintosh", and Android UAs contain "Linux".
_UA_PLATFORMS = (
    ("Android", "Android"),
    ("iPhone", "iOS"),
    ("iPad", "iPadOS"),
    ("Macintosh", "macOS"),
    ("Windows", "Windows"),
    ("Linux", "Linux"),
)


def _device_platform(data, user_agent):
    """Name the operating system behind a failed upload.

    getHighEntropyValues() is Chromium-only — Safari and Firefox expose no
    userAgentData at all, which is precisely the iOS population the HEIC
    timeouts come from. So the client hint is preferred and the UA string is
    the fallback, the same order Sentry's relay and BugSnag use. Previously
    this line was hardcoded to "Android", which mislabelled every non-Android
    reporter in the one mail meant to diagnose their device.
    """
    hinted = _beacon_field(data.get("platform") or "", 20)
    if hinted:
        return hinted
    for needle, name in _UA_PLATFORMS:
        if needle in user_agent:
            return name
    return "unbekannt"


def _photo_report_mailto(ref, stage, data):
    """Compose the whole mailto server-side.

    The diagnostics are already here, and building the link on the server keeps
    the Service Desk address out of the page source. Mail to it opens a
    confidential issue, so the photo and the device details stay internal.
    """
    body = "\n".join(
        [
            "Bitte hängen Sie das Foto an diese E-Mail an, das nicht",
            "hochgeladen werden konnte. Ohne die Originaldatei können wir",
            "den Fehler nicht nachstellen.",
            "",
            "Womit haben Sie das Foto aufgenommen bzw. woher stammt es",
            "(z. B. Kamera-App, Google Fotos, WhatsApp)?",
            "",
            # The picker shape below is a machine guess at the same thing. Asking
            # outright is what confirms it, and it is the one question whose
            # answer the browser cannot supply.
            "War das Foto auf dem Handy gespeichert, oder lag es nur in der",
            "Cloud und musste erst geladen werden?",
            "",
            "",
            "--- Technische Angaben, bitte unverändert lassen ---",
            f"Referenz: {ref}",
            f"Schritt: {stage}",
            f"Dateityp: {_beacon_field(data.get('type') or data.get('ext') or 'unbekannt', 40)}",
            f"Dateigröße: {_beacon_field(data.get('size'), 20)}",
            # Which picker produced the file, inferred from the name shape: the
            # Android photo picker synthesises a numeric name, DocumentsUI passes
            # the gallery's own. That decides whether the bytes stay readable.
            f"Auswahl: {_beacon_field(data.get('name') or 'unbekannt', 10)}",
            f"Browser: {request.user_agent.string[:200]}",
            # The UA says "Android 10; K" whatever the phone is, so without the
            # client hint the support mail cannot name the device that failed.
            f"Gerät: {_beacon_field(data.get('model') or 'unbekannt', 40)}"
            f" ({_device_platform(data, request.user_agent.string)}"
            f" {_beacon_field(data.get('osVersion') or '?', 20)})",
        ]
    )
    query = urlencode(
        {"subject": f"Foto-Upload Fehler {ref}", "body": body}, quote_via=quote
    )
    return f"mailto:{current_app.config['PHOTO_SUPPORT_EMAIL']}?{query}"


@report.route("/melden/foto-fehler", methods=["POST"])
@limiter.limit("10 per minute")
def photo_failure():
    """Record a photo that the browser could not prepare for upload.

    The conversion runs entirely client-side, so without this the failure is
    invisible here: the report is simply never submitted and the Melder gives up.
    """
    data = request.get_json(silent=True) or {}
    stage = _beacon_field(data.get("stage"), 40)

    # Counted server-side so the tally survives a reload, and so the support
    # address is never rendered into the page: anyone holding it can open
    # issues in the tracker.
    failures = session.get("photo_failures", 0) + 1
    session["photo_failures"] = failures

    # Short handle shared by the log line and the mail subject, so a report that
    # arrives by email can be matched to what actually broke.
    ref = secrets.token_hex(3).upper()
    current_app.logger.warning(
        "Photo pipeline failed: ref=%s n=%s stage=%s error=%s size=%s mtime=%s"
        " type=%s ext=%s name=%s model=%s os=%s osv=%s ua=%s",
        ref,
        failures,
        stage,
        _beacon_field(data.get("error"), 200),
        _beacon_field(data.get("size"), 20),
        _beacon_field(data.get("mtime"), 20),
        _beacon_field(data.get("type"), 40),
        _beacon_field(data.get("ext"), 10),
        _beacon_field(data.get("name"), 10),
        _beacon_field(data.get("model"), 40),
        _device_platform(data, request.user_agent.string),
        _beacon_field(data.get("osVersion"), 20),
        request.user_agent.string[:200],
    )

    if failures < current_app.config["PHOTO_ESCALATE_AFTER"]:
        return "", 204

    return jsonify({"mailto": _photo_report_mailto(ref, stage, data)}), 200


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
        form_data["identical_finder_reporter"] = (
            "y"
            if _is_checkbox_true(request.form.get("identical_finder_reporter"))
            else ""
        )

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

    # Map latitude/longitude errors to 'coordinates' — the DOM has id="error-coordinates",
    # not id="error-latitude" / id="error-longitude" (those elements don't exist).
    if "latitude" in errors or "longitude" in errors:
        coord_msgs = errors.pop("latitude", []) + errors.pop("longitude", [])
        errors["coordinates"] = coord_msgs[:1]  # Show first relevant message

    if is_valid:
        # Return a trigger to advance to next step + clear any previous errors via OOB
        visible_fields = get_visible_error_fields(step)
        clear_html = render_template(
            "report/partials/_clear_errors.html", fields=visible_fields, step=step
        )
        response = make_response(clear_html)
        response.headers["HX-Trigger"] = json.dumps(
            {"stepValid": {"step": step, "nextStep": step + 1}}
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

    is_identical = _is_checkbox_true(request.form.get("identical_finder_reporter"))

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
        "identical_finder": _is_checkbox_true(
            request.form.get("identical_finder_reporter")
        ),
        "finder_name": _get_finder_name(request.form),
        "feedback_source": _get_feedback_source_display(
            request.form.get("feedback_source", "")
        ),
        "feedback_detail": request.form.get("feedback_detail", ""),
    }

    return render_template("report/partials/_review_content.html", review=review_data)


# Helper functions for review display
def _get_choice_display(selected_value, choices):
    """Convert a choice value to its display label."""
    for value, label in choices:
        if value == selected_value:
            return label
    return "-"


def _get_gender_display(gender_value):
    """Convert gender field value to display text."""
    from app.forms import GENDER_CHOICES

    return _get_choice_display(gender_value, GENDER_CHOICES)


def _get_location_description_display(location_value):
    """Convert location description value to display text."""
    from app.forms import LOCATION_DESCRIPTION_CHOICES

    return _get_choice_display(location_value, LOCATION_DESCRIPTION_CHOICES)


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
