from flask import (
    Blueprint,
    abort,
    current_app,
    render_template,
    send_from_directory,
)
from flask_login import current_user
from sqlalchemy import select
from sqlalchemy.orm import contains_eager

from app.auth import log_in
from app.database.models import (
    TblFundorte,
    TblMeldungen,
    TblMeldungUser,
    TblUsers,
    UserRole,
)
from app.extensions import db

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

    # Scope by the melduser link, never by user_kontakt: the address is
    # unverified, so anyone knowing it could file under it and read these.
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
        .order_by(TblMeldungen.id.desc())
    )

    sichtungen = db.session.scalars(stmt).all()

    return render_template(
        "provider/melder.html",
        reported_sightings=sichtungen,
        report_user_id=usrid,
    )


@provider.route("/sichtungen/<usrid>/images/<path:filename>")
def report_img(usrid, filename):
    """Serve a report photo to whoever holds the link it was filed under."""
    # Same ownership rule as melder_index.
    owns_image = db.session.scalar(
        select(TblFundorte.id)
        .join(TblMeldungen, TblMeldungen.fo_zuordnung == TblFundorte.id)
        .join(TblMeldungUser, TblMeldungUser.id_meldung == TblMeldungen.id)
        .join(TblUsers, TblUsers.id == TblMeldungUser.id_user)
        .where(TblFundorte.ablage == filename, TblUsers.user_id == usrid)
    )
    if not owns_image:
        abort(403)

    return send_from_directory(
        current_app.config["UPLOAD_FOLDER"], filename, mimetype="image/webp"
    )
