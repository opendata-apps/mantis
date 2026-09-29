import json
import secrets
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urlencode

from email_validator import validate_email
from flask import (
    Blueprint,
    abort,
    current_app,
    jsonify,
    make_response,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user
from sqlalchemy import select

from app.auth import log_in
from app.database.feedback_type import FeedbackSource
from app.database.models import (
    TblFundorte,
    TblMeldungen,
    TblMeldungUser,
    TblUserFeedback,
    TblUsers,
    UserRole,
)
from app.extensions import db, limiter
from app.forms import (
    MantisSightingForm,
    minimum_sighting_date,
)
from app.tools.coordinate_validation import (
    in_range,
    parse_coordinate,
)
from app.tools.gemeinde_finder import get_amt_enriched
from app.tools.gen_user_id import get_new_id
from app.tools.location_enrichment import calculate_spatial_fields
from app.tools.report_images import (
    BlankImageError,
    InvalidImageError,
    process_uploaded_image,
)

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
    }

    genders = {"art_m": 0, "art_w": 0, "art_n": 0, "art_o": 0, "art_f": 0}
    field_name = gender_mapping.get(selected_gender_value)
    if field_name:
        genders[field_name] = 1
    # For "Unbekannt" or empty selection, all fields remain 0
    return genders


def _errors_by_slot(errors):
    """Field errors re-keyed to the error container that displays them.

    Both coordinates share id="error-coordinates"; there is no per-axis slot.
    """
    by_slot = dict(errors)
    coordinate_messages = by_slot.pop("latitude", []) + by_slot.pop("longitude", [])
    if coordinate_messages:
        by_slot["coordinates"] = coordinate_messages[:1]
    return by_slot


def _validation_error_response(errors):
    """Field-level rejection in the shape `showServerErrors` expects."""
    return jsonify(
        {
            "success": False,
            "error": "Ungültige Formulardaten.",
            "errors": _errors_by_slot(errors),
        }
    ), 400


def _normalized_contact(email):
    """The stored form of a contact address; falsy input passes through.

    Lowercases the domain and applies NFC. Assumes the address already passed
    MantisSightingForm validation.
    """
    if not email:
        return email
    return validate_email(email, check_deliverability=False).normalized


def _resolve_reporter(usrid, email):
    """Find the reporter this submission belongs to, or None to create one.

    A link in the URL wins outright. Otherwise the remember cookie may hold the
    link this browser last reported with; the address only breaks the tie on top
    of it, never grants on its own.
    """
    if usrid:
        return db.session.scalar(select(TblUsers).where(TblUsers.user_id == usrid))

    contact = _normalized_contact(email)
    if (
        contact
        and current_user.is_authenticated
        and current_user.user_rolle == UserRole.REPORTER
        and current_user.user_kontakt == contact
    ):
        # Unwrap the proxy: log_in stores what it gets as current_user, and a
        # proxy stored there resolves to itself.
        return current_user._get_current_object()
    return None


def _create_user(name, email, role=UserRole.REPORTER):
    """Store the validated display name without splitting or abbreviating it."""
    user_id = get_new_id()
    user = TblUsers()
    user.user_id = user_id
    user.user_name = name
    user.user_rolle = str(role)
    user.user_kontakt = _normalized_contact(email)
    return user


def _save_report(form, reporter, image_path):
    """Write the finder, feedback, location, sighting and link rows and commit."""
    finder = None
    if not form.identical_finder_reporter.data and form.finder_name.data:
        finder = _create_user(
            form.finder_name.data,
            "",
            role=UserRole.FINDER,
        )
        db.session.add(finder)
        db.session.flush()

    if form.feedback_source.data and not reporter.feedback_source:
        db.session.add(
            TblUserFeedback(
                user_id=reporter.id,
                feedback_source=form.feedback_source.data,
                source_detail=form.feedback_detail.data,
            )
        )

    lat, lon = form.latitude.data, form.longitude.data
    sighting_date = form.sighting_date.data
    if lat is None or lon is None or sighting_date is None:
        raise RuntimeError("Missing coordinates or date after form validation")
    spatial_fields = calculate_spatial_fields(lat, lon)

    location_description = form.location_description.data
    if not isinstance(location_description, str):
        raise RuntimeError(
            "Expected location description after successful form validation"
        )

    fundort = TblFundorte(
        plz=form.fund_zip_code.data or None,
        ort=form.fund_city.data,
        strasse=form.fund_street.data,
        # AGS spatial data is authoritative for land/kreis;
        # fall back to Nominatim (form) only if spatial lookup missed
        kreis=spatial_fields["kreis"] or form.fund_district.data,
        land=spatial_fields["land"] or form.fund_state.data,
        longitude=lon,
        latitude=lat,
        mtb=spatial_fields["mtb"],
        amt=spatial_fields["amt"],
        beschreibung=int(location_description),
        ablage=image_path or "",
    )
    db.session.add(fundort)
    db.session.flush()

    meldung = TblMeldungen(
        dat_fund_von=sighting_date,
        dat_meld=datetime.now(),
        fo_zuordnung=fundort.id,
        fo_quelle="F",
        tiere=1,
        anm_melder=form.description.data,
        **_set_gender_fields(form.gender.data),
    )
    db.session.add(meldung)
    db.session.flush()

    db.session.add(
        TblMeldungUser(
            id_meldung=meldung.id,
            id_user=reporter.id,
            id_finder=finder.id if finder else None,
        )
    )
    db.session.commit()


@report.route("/melden", methods=["GET", "POST"])
@report.route("/melden/<usrid>", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
@limiter.limit("3 per minute", methods=["POST"])
def melden(usrid=None):
    """Handle mantis sighting report form submission with user prefilling support."""
    form = MantisSightingForm()

    if request.method == "GET":
        user_to_prefill = (
            db.session.scalar(select(TblUsers).where(TblUsers.user_id == usrid))
            if usrid
            else None
        )
        if user_to_prefill:
            form.report_name.data = user_to_prefill.user_name
            form.email.data = user_to_prefill.user_kontakt or ""

        response = make_response(
            render_template(
                "report/report_form.html",
                form=form,
                now=datetime.now,
                minimum_sighting_date=minimum_sighting_date(),
                user_prefilled=bool(user_to_prefill),
                user_has_feedback=bool(
                    user_to_prefill and user_to_prefill.feedback_source is not None
                ),
            )
        )
        if user_to_prefill:
            # A prefilled form embeds the reporter's name + email in the markup;
            # keep it out of search and AI indexes. Pairs with the meta-robots tag
            # in report_form.html (page-level noindex, not a robots.txt Disallow —
            # a disallowed page can't be crawled to read the noindex).
            response.headers["X-Robots-Tag"] = "noindex, nofollow"
        return response

    if request.form.get("honeypot", "").strip():
        abort(403)

    if not form.validate_on_submit():
        return _validation_error_response(form.errors)

    # Bound before the try so the failure path can name the photo even
    # when the save dies before the upload is processed.
    db_image_path = None
    try:
        reporter = _resolve_reporter(usrid, form.email.data)
        if not reporter:
            reporter = _create_user(
                form.report_name.data,
                form.email.data,
            )
            db.session.add(reporter)
            db.session.flush()

        if form.photo.data:
            db_image_path = process_uploaded_image(
                form.photo.data,
                form.sighting_date.data,
                form.fund_city.data,
                reporter.user_id,
            )
        _save_report(form, reporter, db_image_path)

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
            _beacon_field(request.user_agent.string, 200),
        )
        return _validation_error_response(
            {
                "photo": [
                    (
                        "Das Foto enthält kein sichtbares Bild. "
                        "Bitte wählen Sie es erneut aus."
                    )
                ]
            }
        )

    except InvalidImageError as error:
        db.session.rollback()
        return _validation_error_response({"photo": [str(error)]})

    except Exception:
        db.session.rollback()
        if db_image_path:
            (Path(current_app.config["UPLOAD_FOLDER"]) / db_image_path).unlink(
                missing_ok=True
            )
        current_app.logger.exception("Failed to save report")
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Ein Fehler ist beim Speichern Ihrer Meldung aufgetreten.",
                }
            ),
            500,
        )

    # Same rule as melder_index: a submission never replaces
    # another identity, a reviewer's session least of all.
    if not current_user.is_authenticated or current_user.user_id == reporter.user_id:
        log_in(reporter)

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
            "report_name",
            "email",
            "identical_finder_reporter",
            "finder_name",
            "feedback_source",
            "feedback_detail",
        ],
        4: [],  # Review step has no specific field validation
    }
    return step_fields.get(step, [])


def get_visible_error_fields(step):
    """Return field names that have visible error containers (for OOB clearing).

    Note: Only includes fields rendered via render_form_field macro (which creates error divs).
    Excludes: latitude/longitude (use 'coordinates'),
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
        3: ["report_name", "email", "finder_name"],
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

    if not in_range(lat, lon):
        return jsonify({}), 400

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
    if not isinstance(value, (str, int, float)):
        return ""
    printable = "".join(char if char.isprintable() else " " for char in str(value))
    return " ".join(printable.split())[:limit]


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

    Prefers the client hint; getHighEntropyValues() is Chromium-only, so Safari
    and Firefox (the iOS population) fall back to the UA string.
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
            (
                f"Gerät: {_beacon_field(data.get('model') or 'unbekannt', 40)}"
                f" ({_device_platform(data, request.user_agent.string)}"
                f" {_beacon_field(data.get('osVersion') or '?', 20)})"
            ),
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
    request.max_content_length = 8 * 1024
    data = request.get_json(silent=True)
    if data is None:
        data = {}
    if not isinstance(data, dict):
        abort(400)
    stage = _beacon_field(data.get("stage"), 40)

    # Offer email support after repeated failures. This is a UX threshold,
    # not proof of a real browser failure or permission to create tickets.
    failures = session.get("photo_failures", 0) + 1
    session["photo_failures"] = failures

    # Short handle shared by the log line and the mail subject, so a report that
    # arrives by email can be matched to what actually broke.
    ref = secrets.token_hex(3).upper()
    current_app.logger.warning(
        "Photo pipeline failed: ref=%s n=%s stage=%s error=%s size=%s mtime=%s"
        " type=%s ext=%s name=%s probe=%s model=%s os=%s osv=%s ua=%s",
        ref,
        failures,
        stage,
        _beacon_field(data.get("error"), 200),
        _beacon_field(data.get("size"), 20),
        _beacon_field(data.get("mtime"), 20),
        _beacon_field(data.get("type"), 40),
        _beacon_field(data.get("ext"), 10),
        _beacon_field(data.get("name"), 10),
        _beacon_field(data.get("probe"), 60),
        _beacon_field(data.get("model"), 40),
        _device_platform(data, request.user_agent.string),
        _beacon_field(data.get("osVersion"), 20),
        _beacon_field(request.user_agent.string, 200),
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

    form = MantisSightingForm(formdata=request.form, meta={"csrf": False})

    form.validate()
    errors = {name: form.errors[name] for name in step_fields if name in form.errors}

    if not errors:
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
    # Return inline error messages via OOB swaps
    return render_template(
        "report/partials/_validation_errors.html", errors=_errors_by_slot(errors)
    )


@report.route("/melden/toggle-finder", methods=["POST"])
def toggle_finder():
    """HTMX endpoint to toggle finder fields visibility."""
    if not _is_partial_request():
        abort(400)

    is_identical = _is_checkbox_true(request.form.get("identical_finder_reporter"))

    if is_identical:
        return render_template("report/partials/_finder_fields.html", show=False)
    # Return visible finder fields
    form = MantisSightingForm()
    return render_template("report/partials/_finder_fields.html", show=True, form=form)


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

    form = MantisSightingForm(formdata=request.form, meta={"csrf": False})
    return render_template(
        "report/partials/_review_content.html",
        form=form,
        sighting_date=_format_date(request.form.get("sighting_date", "")),
        coordinates=_format_coordinates(
            request.form.get("latitude", ""), request.form.get("longitude", "")
        ),
        identical_finder=_is_checkbox_true(
            request.form.get("identical_finder_reporter")
        ),
        finder_name=form.finder_name.data or "-",
    )


def _format_date(date_str):
    """Format date string for display."""
    if not date_str:
        return "-"
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%d.%m.%Y")
    except ValueError:
        return date_str


def _format_coordinates(lat, lng):
    """Format coordinates for display."""
    latitude, longitude = parse_coordinate(lat), parse_coordinate(lng)
    if latitude is None or longitude is None:
        return "-"
    return f"{latitude:.6f}, {longitude:.6f}"
