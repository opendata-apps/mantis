from flask import (
    render_template,
    Blueprint,
    send_from_directory,
    abort,
    current_app,
)
from flask_login import current_user, login_required

from app.extensions import db
from app.auth import log_in
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
    user = db.session.scalar(select(TblUsers).where(TblUsers.user_id == usrid))

    if not user or user.user_rolle not in (UserRole.REPORTER, UserRole.REVIEWER):
        abort(404)

    # Only when the visitor holds no other identity: Reporter A following
    # Reporter B's link must not take it over, nor a reviewer lose their session.
    if not current_user.is_authenticated or current_user.user_id == usrid:
        log_in(user)

    image_path = current_app.config["UPLOAD_FOLDER"]

    # Scope by the melduser link, never by user_kontakt — as this did until
    # 2026-09. The email field is unverified, so anyone knowing an address could
    # file one sighting under it and read that owner's coordinates and photos.
    stmt = (
        select(TblMeldungen)
        .join(TblMeldungen.reporter_link)
        .join(TblMeldungen.fundort)
        .join(TblFundorte.location_type)
        .options(
            contains_eager(TblMeldungen.fundort).contains_eager(
                TblFundorte.location_type
            )
        )
        .where(TblMeldungUser.id_user == user.id)
    )

    sichtungen = db.session.scalars(stmt).all()

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
    if current_user.user_rolle == UserRole.REVIEWER:
        return send_from_directory(
            current_app.config["UPLOAD_FOLDER"], filename, mimetype="image/webp"
        )

    # Same ownership rule as melder_index.
    owns_image = db.session.scalar(
        select(TblFundorte.id)
        .join(TblMeldungen, TblMeldungen.fo_zuordnung == TblFundorte.id)
        .join(TblMeldungUser, TblMeldungUser.id_meldung == TblMeldungen.id)
        .where(
            TblFundorte.ablage == filename,
            TblMeldungUser.id_user == current_user.id,
        )
    )
    if not owns_image:
        abort(403)

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"], filename, mimetype="image/webp"
    )
