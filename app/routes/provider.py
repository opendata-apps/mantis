from flask import session  # import session
from flask import render_template, Blueprint, send_from_directory
from app import db
from flask import abort
from app.config import Config
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
    # Fetch the user based on the 'usrid' parameter
    user = TblUsers.query.filter_by(user_id=usrid).first()
    # If the user doesn't exist or the role isn't 9, return 404
    if not user or (user.user_rolle != "1" and user.user_rolle != "9"):
        abort(404)

    # Store the userid in session
    session["user_id"] = usrid

    image_path = Config.UPLOAD_FOLDER.replace("app/", "")

    # Using SQLAlchemy syntax for querying
    sichtungen_query = (
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
        .filter(TblUsers.user_id == usrid)
        .all()
    )

    sichtungen = []
    for sighting in sichtungen_query:
        sighting_dict = sighting._asdict()
        if sighting_dict["dat_bear"] is None:
            sighting_dict["dat_bear"] = "noch nicht geprüft"
        sichtungen.append(sighting_dict)

    return render_template(
        "provider/melder.html", reported_sightings=sichtungen, image_path=image_path
    )


@provider.route("/<path:filename>")
def report_Img(filename):
    "Return the image file for the report with the given filename."
    return send_from_directory(
        Config["UPLOAD_PATH"], filename, mimetype="image/webp", as_attachment=False
    )
