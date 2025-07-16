from flask import session  # import session
from flask import render_template, Blueprint, send_from_directory
from app import db
from flask import abort
from app.database.models import (
    TblFundorte,
    TblMeldungen,
    TblUsers,
    TblFundortBeschreibung,
    TblMeldungUser,
)

# Blueprints
provider = Blueprint("provider", __name__)


@provider.route("/report/<usrid>")
@provider.route("/sichtungen/<usrid>")
def melder_index(usrid):
    "Index page for the provider. The users reports are displayed here."
    # First find the user making the request with role 1 or 9
    user = TblUsers.query.filter_by(user_id=usrid).first()

    # If the user doesn't exist or the role isn't 1 or 9, return 404
    if not user or (user.user_rolle != "1" and user.user_rolle != "9"):
        abort(404)

    # Store the userid in session
    session["user_id"] = usrid

    from flask import current_app
    image_path = current_app.config['UPLOAD_FOLDER'].replace("app/", "")

    # Get the user's email if provided
    user_email = user.user_kontakt if user.user_kontakt else None

    # Base query with all the necessary joins
    base_query = (
        db.session.query(
            TblMeldungen.id,
            TblMeldungen.dat_fund_von,
            TblMeldungen.dat_fund_bis, 
            TblMeldungen.dat_meld,
            TblMeldungen.dat_bear,
            TblMeldungen.tiere,
            TblMeldungen.fo_quelle,
            TblMeldungen.art_m,
            TblMeldungen.art_w,
            TblMeldungen.art_n,
            TblMeldungen.art_o,
            TblMeldungen.art_f,
            TblMeldungen.anm_melder,
            TblFundortBeschreibung.beschreibung,
            TblUsers.user_id,
            TblUsers.user_name,
            TblUsers.user_kontakt,
            TblFundorte.plz,
            TblFundorte.ort,
            TblFundorte.strasse,
            TblFundorte.land,
            TblFundorte.kreis,
            TblFundorte.longitude,
            TblFundorte.latitude,
            TblFundorte.ablage,
        )
        .join(TblMeldungUser, TblMeldungen.id == TblMeldungUser.id_meldung)
        .join(TblUsers, TblMeldungUser.id_user == TblUsers.id)
        .join(TblFundorte, TblMeldungen.fo_zuordnung == TblFundorte.id)
        .join(
            TblFundortBeschreibung,
            TblFundorte.beschreibung == TblFundortBeschreibung.id,
        )
    )

    # Apply email filter only if user has an email
    if user_email:
        sichtungen_query = base_query.filter(TblUsers.user_kontakt == user_email).all()
    else:
        sichtungen_query = base_query.filter(TblUsers.user_id == usrid).all()

    # Process query results
    sichtungen = []
    for sighting in sichtungen_query:
        sighting_dict = sighting._asdict()
        sighting_dict["dat_bear"] = sighting_dict["dat_bear"] or "noch nicht geprüft"
        sichtungen.append(sighting_dict)

    return render_template(
        "provider/melder.html",
        reported_sightings=sichtungen,
        image_path=image_path
    )


@provider.route("/<path:filename>")
def report_Img(filename):
    "Return the image file for the report with the given filename."

    from flask import current_app
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'], filename,
        mimetype="image/webp", as_attachment=False
    )
