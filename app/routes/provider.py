from flask import session  # import session
from flask import render_template, Blueprint, send_from_directory
from app import db
from flask import abort
from app.config import Config
from app.database.models import TblUsers
from sqlalchemy import text

# Blueprints
provider = Blueprint('provider', __name__)


@provider.route('/melder/<usrid>')
def melder_index(usrid):
    # Fetch the user based on the 'usrid' parameter
    user = TblUsers.query.filter_by(user_id=usrid).first()
    # If the user doesn't exist or the role isn't 9, return 404
    if not user or user.user_rolle != '1':
        abort(404)

    # Store the userid in session
    session['user_id'] = usrid

    image_path = Config.UPLOAD_FOLDER.replace("app/", "")
    sql = text(f"""
    select
      me.id, dat_fund_von, dat_fund_bis, dat_meld,
      coalesce(dat_bear::text, 'noch nicht geprüft') as dat_bear,
      tiere, fo_quelle, art_m, art_w, art_n, art_o, art_f,
      anm_melder, be.beschreibung, user_id,  user_name, user_kontakt,
      plz, ort, strasse, land, kreis, longitude, latitude, ablage
    from melduser mu
      left join meldungen me on mu.id_meldung = me.id
      left join users us on mu.id_user = us.id
      left join fundorte fo on me.fo_zuordnung = fo.id
     left join beschreibung be on fo.beschreibung = be.id
    where us.user_id = '{usrid}';
    """)
    sichtungen = []
    with db.engine.connect() as conn:
        result = conn.execute(sql)
        for row in result:
            row = row._mapping
            res = dict((name, val) for name, val in row.items())
            sichtungen.append(res)
    return render_template('provider/melder.html',
                           reported_sightings=sichtungen,
                           image_path=image_path)


@provider.route('/<path:filename>')
def report_Img(filename):
    return send_from_directory(Config['UPLOAD_PATH'],
                               filename,
                               mimetype='image/webp',
                               as_attachment=False)


