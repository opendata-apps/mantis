from flask import (
    g,
    session,
    render_template,
    Blueprint,
    send_from_directory,
    abort,
    current_app,
)
from app import db
from app.auth import login_required
from sqlalchemy import select
from sqlalchemy.orm import contains_eager
from app.database.models import (
    TblFundorte,
    TblMeldungen,
    TblUsers,
    TblMeldungUser,
    UserRole,
)

# Blueprints
provider = Blueprint("provider", __name__)


@provider.route("/report/<usrid>")
@provider.route("/sichtungen/<usrid>")
def melder_index(usrid):
    "Index page for the provider. The users reports are displayed here."
    # First find the user making the request with role 1 or 9
    user = db.session.scalar(select(TblUsers).where(TblUsers.user_id == usrid))

    # If the user doesn't exist or the role isn't 1 or 9, return 404
    if not user or user.user_rolle not in (UserRole.REPORTER, UserRole.REVIEWER):
        abort(404)

    # Only set session when visitor has no active session or is visiting
    # their own page. This prevents session hijacking when Reporter A
    # clicks Reporter B's link, and preserves reviewer sessions.
    current_user_id = session.get("user_id")
    if not current_user_id or current_user_id == usrid:
        session["user_id"] = usrid
        session.permanent = True

    image_path = current_app.config["UPLOAD_FOLDER"]

    # Get the user's email if provided
    user_email = user.user_kontakt if user.user_kontakt else None

    # Relationship-based query with eager loading
    base_stmt = (
        select(TblMeldungen)
        .join(TblMeldungen.reporter_link)
        .join(TblMeldungUser.reporter)
        .join(TblMeldungen.fundort)
        .join(TblFundorte.location_type)
        .options(
            contains_eager(TblMeldungen.fundort).contains_eager(
                TblFundorte.location_type
            ),
            contains_eager(TblMeldungen.reporter_link).contains_eager(
                TblMeldungUser.reporter
            ),
        )
    )

    # Apply email filter only if user has an email
    if user_email:
        stmt = base_stmt.where(TblUsers.user_kontakt == user_email)
    else:
        stmt = base_stmt.where(TblUsers.user_id == usrid)

    # .unique() deduplicates if melduser has multiple rows per meldung
    sichtungen = db.session.scalars(stmt).unique().all()

    return render_template(
        "provider/melder.html",
        reported_sightings=sichtungen,
        image_path=image_path,
        report_user_id=usrid,
    )


@provider.route("/images/<path:filename>")
@login_required
def report_img(filename):
    """Serve report images — only to the owning reporter or reviewers."""
    user = g.current_user

    # Reviewers can see all images
    if user.user_rolle == "9":
        return send_from_directory(
            current_app.config["UPLOAD_FOLDER"], filename, mimetype="image/webp"
        )

    # Verify reporter owns this image (mirrors melder_index email-grouping logic)
    ownership_query = (
        select(TblFundorte.id)
        .join(TblMeldungen, TblMeldungen.fo_zuordnung == TblFundorte.id)
        .join(TblMeldungUser, TblMeldungUser.id_meldung == TblMeldungen.id)
        .join(TblUsers, TblUsers.id == TblMeldungUser.id_user)
        .where(TblFundorte.ablage == filename)
    )
    if user.user_kontakt:
        ownership_query = ownership_query.where(
            TblUsers.user_kontakt == user.user_kontakt
        )
    else:
        ownership_query = ownership_query.where(TblUsers.user_id == user.user_id)

    if not db.session.scalar(ownership_query):
        abort(403)

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"], filename, mimetype="image/webp"
    )
