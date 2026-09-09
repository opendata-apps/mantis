"""Reviewer workflow: the report list and every action on a single report."""

from datetime import datetime

from flask import (
    abort,
    current_app,
    g,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import contains_eager, joinedload

from flask_login import current_user

from app.auth import log_in, reviewer_required
from app.database.models import (
    STATUS_FILTERS,
    ReportStatus,
    TblFundorte,
    TblMeldungen,
    TblMeldungUser,
    TblUsers,
    UserRole,
)
from app.extensions import db
from app.routes.admin.blueprint import admin
from app.tools.location_enrichment import recalculate_amt_mtb
from app.routes.admin.filters import (
    get_filtered_query,
    get_reviewer_filter_args,
    normalize_filter_status,
)
from app.tools.coordinate_validation import (
    validate_and_normalize_coordinate,
    validate_coordinate_pair,
)
from app.tools.send_reviewer_email import build_email_payload, send_email

# Bounds of the PostgreSQL integer columns the count fields are stored in.
INT32_MIN = -(2**31)
INT32_MAX = 2**31 - 1

# Flags that sit alongside a workflow state rather than replacing it.
REVIEW_FLAGS = frozenset({ReportStatus.INFO.value, ReportStatus.UNKL.value})


def _mark_sighting_updated(sighting: TblMeldungen) -> None:
    """Record the reviewer responsible for the latest mutation."""
    sighting.bearb_id = current_user.user_id


def _commit_or_log(log_context: str) -> bool:
    """Commit the current transaction. Rolls back and returns False on failure.

    The caller decides what a failure looks like: the JSON endpoints answer
    with an error body, the HTMX ones with a bare status.
    """
    try:
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"{log_context}: {e}")
        return False
    return True


def _set_statuses(sighting: TblMeldungen, statuses: list[str]) -> None:
    """Set the canonical statuses array and keep ``deleted`` in step.

    ``TblMeldungen.deleted`` is a deprecated mirror of the DEL status that
    older queries still read. Assigning ``statuses`` directly anywhere else
    would let the two drift apart.
    """
    sighting.statuses = statuses
    sighting.deleted = sighting.is_deleted


def _resolve_filter_status(default: str = "offen") -> str:
    """Resolve current filter status from request payload/args."""
    return normalize_filter_status(
        request.values.get("filter_status") or request.args.get("statusInput"),
        default,
    )


def _load_sighting(report_id: int) -> TblMeldungen | None:
    """Load one report with all relationships populated via eager loading."""
    stmt = (
        select(TblMeldungen)
        .join(TblMeldungen.fundort)
        .join(TblFundorte.location_type)
        .join(TblMeldungen.reporter_link)
        .join(TblMeldungUser.reporter)
        .options(
            contains_eager(TblMeldungen.fundort).contains_eager(
                TblFundorte.location_type
            ),
            contains_eager(TblMeldungen.reporter_link).contains_eager(
                TblMeldungUser.reporter
            ),
            joinedload(TblMeldungen.approver),
        )
        .where(TblMeldungen.id == report_id)
    )
    return db.session.scalars(stmt).unique().first()


def _get_user_report_count(user: TblUsers) -> int:
    """Count total reports by this person (match by email or user ID).

    Cached per-request in g to avoid redundant COUNT queries when
    the same user is looked up across modal open + tab switches.
    """
    cache = g.setdefault("_user_report_counts", {})
    if user.id in cache:
        return cache[user.id]

    if user.user_kontakt:
        count = db.session.scalar(
            select(func.count())
            .select_from(TblMeldungUser)
            .join(TblMeldungUser.reporter)
            .where(TblUsers.user_kontakt == user.user_kontakt)
        )
    else:
        count = db.session.scalar(
            select(func.count())
            .select_from(TblMeldungUser)
            .where(TblMeldungUser.id_user == user.id)
        )
    cache[user.id] = count or 0
    return cache[user.id]


def _load_sighting_for_render(
    report_id: int,
) -> tuple[TblMeldungen | None, TblUsers | None]:
    """Load a report for modal/card rendering."""
    meldung = _load_sighting(report_id)
    if not meldung:
        return None, None
    return meldung, meldung.reporter_link.reporter


def _matches_filter_status(sighting: TblMeldungen, filter_status: str) -> bool:
    """Check whether sighting should stay visible in current filtered list."""
    normalized = normalize_filter_status(filter_status, default="")
    if normalized == "all":
        return True
    attribute = STATUS_FILTERS.get(normalized)
    if attribute:
        return getattr(sighting, attribute)
    # Reviewer default behavior: show non-deleted reports.
    return not sighting.is_deleted


def _render_report_card_or_delete(sighting: TblMeldungen, filter_status: str):
    """Render updated card for HTMX or delete target when it no longer matches filter."""
    if not _matches_filter_status(sighting, filter_status):
        return _hx_delete_response()

    return render_template(
        "admin/partials/_report_card.html",
        sighting=sighting,
        current_filter_status=filter_status,
    )


def _hx_delete_response():
    """Return an empty HTMX response that deletes the target element."""
    response = make_response("", 200)
    response.headers["HX-Reswap"] = "delete"
    return response


def _render_updated_sighting_by_id(report_id: int, filter_status: str):
    """Load updated sighting and return card partial or delete response."""
    rendered_sighting, _ = _load_sighting_for_render(report_id)
    if not rendered_sighting:
        return _hx_delete_response()
    return _render_report_card_or_delete(rendered_sighting, filter_status)


# SECURITY NOTE: the user_id in the URL is the credential — secrets.token_hex(20),
# 160 bits. The risk is leakage through browser history, Referer, or server logs,
# not guessing. See app/auth.py. The admin blueprint is rate-limit exempt, so
# there is no throttle here either (app/factory.py, register_blueprints).
@admin.route("/reviewer")
@admin.route("/reviewer/<usrid>")
def reviewer(usrid=None):
    "This function is used to display the reviewer page"
    if usrid:
        # URL-based login: validate user and establish session
        user = db.session.scalar(select(TblUsers).where(TblUsers.user_id == usrid))
        if not user or user.user_rolle != UserRole.REVIEWER:
            abort(403)
        log_in(user)
    else:
        # Session-based auth (consistent with @reviewer_required)
        if (
            not current_user.is_authenticated
            or current_user.user_rolle != UserRole.REVIEWER
        ):
            abort(403)
        user = current_user
        usrid = user.user_id

    user_name = user.user_name
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 21, type=int)
    filter_args = get_reviewer_filter_args()
    filter_status = filter_args["filter_status"]
    filter_type = filter_args["filter_type"]
    sort_order = request.args.get("sort_order", "id_desc")  # Changed default to desc
    search_query = filter_args["search_query"]
    search_type = filter_args["search_type"]
    date_from = filter_args["date_from"]
    date_to = filter_args["date_to"]
    date_type = filter_args["date_type"]

    if "statusInput" not in request.args and "sort_order" not in request.args:
        return redirect(
            url_for(
                "admin.reviewer",
                statusInput="offen",
                sort_order="id_desc",
            )
        )

    # Get filtered select statement using our reusable function
    stmt = get_filtered_query(
        filter_status=filter_status,
        filter_type=filter_type,
        search_query=search_query,
        search_type=search_type,
        date_from=date_from,
        date_to=date_to,
        date_type=date_type,
    )

    # Apply sort order
    if sort_order == "id_asc":
        stmt = stmt.order_by(TblMeldungen.id.asc())
    elif sort_order == "id_desc":
        stmt = stmt.order_by(TblMeldungen.id.desc())

    paginated_sightings = db.paginate(
        stmt,
        page=page,
        per_page=per_page,
        max_per_page=100,
        error_out=False,
    )

    return render_template(
        "admin/admin.html",
        user_id=usrid,
        paginated_sightings=paginated_sightings,
        reported_sightings=paginated_sightings.items,
        user_name=user_name,
        filters={"status": filter_status, "type": filter_type},
        current_filter_status=filter_status,
        current_sort_order=sort_order,
        search_query=search_query,
        search_type=search_type,
        current_date_type=date_type,
    )


@admin.route("/change_mantis_meta_data/<int:id>", methods=["POST"])
@reviewer_required
def change_mantis_meta_data(id):
    "Change mantis report metadata"
    new_data = request.form.get("new_data")
    fieldname = request.form.get("type")

    # Normalize free-text at the boundary: WTForms is bypassed on this path, so
    # strip here to keep stored values (e.g. anm_bearbeiter) and the Excel export
    # free of stray leading/trailing whitespace.
    if isinstance(new_data, str):
        new_data = new_data.strip()

    if not new_data or not fieldname:
        return jsonify({"error": "Missing data in request"}), 400

    sighting_meldung = db.session.get(TblMeldungen, id)
    if not sighting_meldung:
        return jsonify({"error": "Report not found"}), 404

    requires_fundort = fieldname not in ["fo_quelle", "anm_bearbeiter"]
    if requires_fundort:
        sighting_obj = sighting_meldung.fundort
        if not sighting_obj:
            return jsonify({"error": "Location not found"}), 404
    else:
        sighting_obj = sighting_meldung

    _mark_sighting_updated(sighting_meldung)
    update_fields = {
        "fo_quelle": "fo_quelle",
        "anm_bearbeiter": "anm_bearbeiter",
        "amt": "amt",
        "mtb": "mtb",
        "latitude": "latitude",
        "longitude": "longitude",
        "plz": "plz",
        "ort": "ort",
        "strasse": "strasse",
        "kreis": "kreis",
        "land": "land",
    }

    field_to_update = update_fields.get(fieldname)
    if field_to_update:
        # Normalize coordinate values before storing
        if fieldname in ["latitude", "longitude"]:
            is_valid, normalized_value, error_msg = validate_and_normalize_coordinate(
                new_data, fieldname
            )
            if not is_valid:
                return jsonify({"error": error_msg}), 400
            new_data = normalized_value

        # plz is an integer column; reject non-numeric input at the boundary
        # so the user sees a 400 instead of a generic DB error on commit.
        if fieldname == "plz":
            plz_raw = new_data.strip()
            if not plz_raw.isdigit() or int(plz_raw) > 99999:
                return jsonify({"error": "Invalid ZIP code"}), 400
            new_data = int(plz_raw)

        setattr(sighting_obj, field_to_update, new_data)

        # If coordinates were updated, recalculate AMT and MTB
        if fieldname in ["latitude", "longitude"]:
            recalculate_amt_mtb(sighting_obj)

        if not _commit_or_log(f"Database error updating report {id}"):
            return jsonify({"error": "Database error"}), 500

        current_app.logger.info(
            f"Report {id} metadata updated: {fieldname} to {new_data} by user {sighting_meldung.bearb_id}"
        )
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Invalid field type"}), 400


@admin.route("/update_coordinates/<int:id>", methods=["POST"])
@reviewer_required
def update_coordinates(id):
    """Update both coordinates at once and recalculate AMT/MTB."""
    latitude = (request.form.get("latitude") or "").strip()
    longitude = (request.form.get("longitude") or "").strip()
    if not latitude or not longitude:
        return jsonify({"error": "Missing coordinates"}), 400

    # Validate and normalize both coordinates
    is_valid, normalized_lat, normalized_lon, errors = validate_coordinate_pair(
        latitude, longitude
    )
    if not is_valid:
        return jsonify({"error": errors[0]}), 400

    sighting = db.session.get(TblMeldungen, id)
    if not sighting:
        return jsonify({"error": "Report not found"}), 404

    fundort = sighting.fundort
    if not fundort:
        return jsonify({"error": "Location not found"}), 404

    # Update coordinates and recalculate
    fundort.latitude = normalized_lat
    fundort.longitude = normalized_lon
    recalculate_amt_mtb(fundort)

    _mark_sighting_updated(sighting)
    if not _commit_or_log(f"Error updating coordinates for report {id}"):
        return jsonify({"error": "Failed to update coordinates"}), 500

    return jsonify(
        {"success": True, "amt": fundort.amt or "", "mtb": fundort.mtb or ""}
    )


@admin.route("/update_address/<int:id>", methods=["POST"])
@reviewer_required
def update_address(id):
    """Update reverse-geocoded address fields after coordinate changes."""
    sighting = db.session.get(TblMeldungen, id)
    if not sighting:
        return jsonify({"error": "Report not found"}), 404

    fundort = sighting.fundort
    if not fundort:
        return jsonify({"error": "Location not found"}), 404

    # Keep existing values when geocoder returns empty strings.
    plz_raw = (request.form.get("plz") or "").strip()
    ort = (request.form.get("ort") or "").strip()
    strasse = (request.form.get("strasse") or "").strip()
    kreis = (request.form.get("kreis") or "").strip()
    land = (request.form.get("land") or "").strip()

    if plz_raw:
        if not plz_raw.isdigit():
            return jsonify({"error": "Invalid ZIP code"}), 400
        plz_value = int(plz_raw)
        # German postal codes are max 5 digits; reject oversized numeric input.
        if plz_value > 99999:
            return jsonify({"error": "Invalid ZIP code"}), 400
        fundort.plz = plz_value
    if ort:
        fundort.ort = ort
    if strasse:
        fundort.strasse = strasse
    if kreis:
        fundort.kreis = kreis
    if land:
        fundort.land = land

    _mark_sighting_updated(sighting)
    if not _commit_or_log(f"Failed to update address for report {id}"):
        return jsonify({"error": "Failed to update address"}), 500

    return jsonify({"success": True}), 200


@admin.route("/admin/images/<path:filename>")
@reviewer_required
def report_img(filename):
    """Serve report images securely from the upload folder."""
    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"], filename, mimetype="image/webp"
    )


def _notify_reporter_of_approval(report_id: int) -> None:
    """Tell the reporter their sighting was accepted.

    Never raises: a failed notification must not undo an approval that is
    already committed.
    """
    # _load_sighting() populates the fundort/reporter relationships the payload
    # reads; without it every attribute below would emit its own query.
    meldung = _load_sighting(report_id)
    if not meldung:
        current_app.logger.error(
            f"Sighting {report_id} not found while building email payload."
        )
        return

    payload = build_email_payload(meldung)
    if not payload["user_kontakt"]:
        # Contact is optional on the report form, so a blank one is routine,
        # not an error — at ERROR it drowns out real SMTP faults.
        current_app.logger.warning(
            f"Email not sent for sighting {report_id}. No email address found."
        )
        return

    try:
        send_email(payload)
    except Exception as e:
        current_app.logger.error(f"Email not sent for sighting {report_id}. Error: {e}")


@admin.route("/toggle_approve_sighting/<int:id>", methods=["POST"])
@reviewer_required
def toggle_approve_sighting(id):
    """Toggle APPR/OPEN workflow state.

    A report with any active review flag (UNKL "Unklar" or INFO "Informiert")
    cannot be approved — the reviewer must resolve the open review concern
    and clear the flag first. Un-approving preserves flags.
    """

    sighting = db.session.get(TblMeldungen, id)
    if not sighting:
        current_app.logger.error(f"Sighting {id} not found for approval toggle.")
        return "", 404

    # Toggle between APPR and OPEN.
    # Un-approving preserves flags (re-opening keeps existing context).
    if sighting.is_approved:
        flags = [s for s in (sighting.statuses or []) if s in REVIEW_FLAGS]
        _set_statuses(sighting, [ReportStatus.OPEN.value] + flags)
        sighting.dat_bear = None
    else:
        # Any active review flag blocks approval — open concerns must be
        # resolved explicitly, not silently dropped on accept.
        if sighting.is_unclear or sighting.needs_info:
            return "", 400
        _set_statuses(sighting, [ReportStatus.APPR.value])
        sighting.dat_bear = datetime.now()
    _mark_sighting_updated(sighting)

    if not _commit_or_log(f"Failed to toggle approval for sighting {id}"):
        return "", 500

    current_app.logger.debug(
        f"Sighting {id} statuses toggled to {sighting.statuses}. dat_bear set to {sighting.dat_bear}"
    )

    if current_app.config.get("REVIEWERMAIL", False) and sighting.is_approved:
        _notify_reporter_of_approval(id)

    filter_status = _resolve_filter_status()
    response = make_response(_render_updated_sighting_by_id(id, filter_status))
    # CSP-safe modal close: body listens for `mantis:modal-close` and closes
    # the dialog. Replaces the previous hx-on::after-request inline handler
    # on the Annehmen button. No-op when no modal is open (the report-card
    # variant of this button calls the endpoint without a modal). Namespaced
    # per htmx's `<ns>:<event>` convention to avoid collisions.
    response.headers["HX-Trigger"] = "mantis:modal-close"
    return response


@admin.route("/modal/<int:id>", methods=["GET"])
@reviewer_required
def modal_open(id):
    """Open reviewer modal content (default: general tab)."""
    sighting, user = _load_sighting_for_render(id)
    if not sighting or not user:
        abort(404, description="Report not found")

    filter_status = _resolve_filter_status()
    edit_mode = request.args.get("edit") == "1"
    is_approved = sighting.is_approved
    editable = not is_approved or edit_mode
    return render_template(
        "admin/partials/_modal_open.html",
        sighting=sighting,
        feedback=user.feedback_source,
        user_report_count=_get_user_report_count(user),
        is_approved=is_approved,
        editable=editable,
        active_tab="general",
        edit_mode=edit_mode,
        filter_status=filter_status,
    )


@admin.route("/modal/<string:tab>/<int:id>", methods=["GET"])
@reviewer_required
def modal_tab(tab: str, id: int):
    """Switch modal tab content via HTMX with OOB tab/footer updates."""
    if tab not in {"general", "location"}:
        abort(404, description="Tab not found")

    sighting, user = _load_sighting_for_render(id)
    if not sighting or not user:
        abort(404, description="Report not found")

    filter_status = _resolve_filter_status()
    edit_mode = request.args.get("edit") == "1"
    is_approved = sighting.is_approved
    editable = not is_approved or edit_mode
    return render_template(
        "admin/partials/_tab_response.html",
        sighting=sighting,
        feedback=user.feedback_source,
        user_report_count=_get_user_report_count(user),
        is_approved=is_approved,
        editable=editable,
        active_tab=tab,
        edit_mode=edit_mode,
        filter_status=filter_status,
    )


@admin.route("/toggle_flag/<int:id>", methods=["POST"])
@reviewer_required
def toggle_flag(id):
    """Toggle INFO/UNKL flag while preserving workflow state."""
    flag = (request.form.get("flag") or "").strip().upper()
    if flag not in {ReportStatus.INFO.value, ReportStatus.UNKL.value}:
        return "", 400

    sighting = db.session.get(TblMeldungen, id)
    if not sighting:
        return "", 404
    if sighting.is_deleted:
        return "", 400
    if sighting.is_approved:
        return "", 400

    statuses = list(sighting.statuses or [ReportStatus.OPEN.value])
    if flag in statuses:
        statuses = [s for s in statuses if s != flag]
    else:
        statuses.append(flag)

    workflow_states = {
        ReportStatus.OPEN.value,
        ReportStatus.APPR.value,
        ReportStatus.DEL.value,
    }
    if not any(s in workflow_states for s in statuses):
        statuses.insert(0, ReportStatus.OPEN.value)

    is_valid, error = ReportStatus.validate_combination(statuses)
    if not is_valid:
        return "", 400

    _set_statuses(sighting, statuses)
    _mark_sighting_updated(sighting)

    if not _commit_or_log(f"Failed to toggle flag for sighting {id}"):
        return "", 500

    filter_status = _resolve_filter_status()
    # OOB: keep the modal footer in sync with the new flag state so the
    # "Annehmen" button enables/disables live when UNKL is toggled. This
    # route is only called from the open modal, so the target always exists.
    modal_actions_html = render_template(
        "admin/partials/_modal_actions.html",
        sighting=sighting,
        is_approved=sighting.is_approved,
        editable=not sighting.is_approved,
        edit_mode=False,
        active_tab="general",
        filter_status=filter_status,
    )
    response = make_response(_render_updated_sighting_by_id(id, filter_status))
    response.set_data(
        response.get_data(as_text=True)
        + f'<div id="modal-actions" hx-swap-oob="innerHTML">{modal_actions_html}</div>'
    )
    return response


@admin.route("/delete_sighting/<int:id>", methods=["POST"])
@reviewer_required
def delete_sighting(id):
    "Soft-delete sighting based on id"
    sighting = db.session.get(TblMeldungen, id)
    if not sighting:
        return "", 404

    # DEL is exclusive, so it replaces every other status.
    _set_statuses(sighting, [ReportStatus.DEL.value])
    _mark_sighting_updated(sighting)

    if not _commit_or_log(f"Failed to delete sighting {id}"):
        return "", 500

    filter_status = _resolve_filter_status()
    return _render_updated_sighting_by_id(id, filter_status)


@admin.route("/undelete_sighting/<int:id>", methods=["POST"])
@reviewer_required
def undelete_sighting(id):
    "Undelete sighting based on id"
    sighting = db.session.get(TblMeldungen, id)
    if not sighting:
        return "", 404

    # Restoring returns the report to the review queue with no flags.
    _set_statuses(sighting, [ReportStatus.OPEN.value])
    _mark_sighting_updated(sighting)

    if not _commit_or_log(f"Failed to undelete sighting {id}"):
        return "", 500

    filter_status = _resolve_filter_status()
    return _render_updated_sighting_by_id(id, filter_status)


@admin.route("/change_mantis_count/<int:id>", methods=["POST"])
@reviewer_required
def change_mantis_count(id):
    "Change mantis count for a specific type"
    new_count_raw = request.form.get("new_count")
    mantis_type = (request.form.get("type") or "").strip()
    sighting = db.session.get(TblMeldungen, id)
    if sighting is None:
        abort(404, description="Sighting not found")

    count_fields = {
        "Männchen": "art_m",
        "Weibchen": "art_w",
        "Nymphe": "art_n",
        "Oothek": "art_o",
        "Andere": "art_f",
        "Anzahl": "tiere",
    }
    field = count_fields.get(mantis_type)
    if field is None:
        return jsonify({"error": "Invalid mantis type"}), 400

    if new_count_raw is None or str(new_count_raw).strip() == "":
        return jsonify({"error": "Missing count value"}), 400

    try:
        new_count = int(str(new_count_raw).strip())
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid count value"}), 400

    if not (INT32_MIN <= new_count <= INT32_MAX):
        return jsonify({"error": "Count value out of range"}), 400

    if new_count < 0:
        return jsonify({"error": "Count must be non-negative"}), 400

    setattr(sighting, field, new_count)

    _mark_sighting_updated(sighting)
    if not _commit_or_log(f"Failed to update mantis count for sighting {id}"):
        return jsonify({"error": "Failed to update mantis count"}), 500

    return jsonify({"success": True})
