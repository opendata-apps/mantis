from flask import render_template, request, Blueprint
from app import config
from app import db
from flask import send_from_directory
from sqlalchemy import text
from app.routes.reviewer_form import ReviewerForm
from werkzeug.datastructures import MultiDict

# Blueprints
review = Blueprint('reviewer', __name__)


# @review.route('/imagedata/<path:filename>', methods=["GET"])
# def imagedata(filename):
#     UPLOAD_PATH = config.Config.UPLOAD_PATH
#     return send_from_directory(UPLOAD_PATH,
#                                filename,
#                                mimetype='image/webp')


# @review.route('/reviewer')
# @review.route('/reviewer', methods=['POST'])
# def review_index():
#     res = {'Anmerkung': 'Keinen Datensatz mit dieser ID gefunden!'}
#     if request.method == 'POST':
#         try:
#             id = int(request.form['id'])
#         except:
#             form = {}
#             res = {'Anmerkung': 'Keinen Datensatz mit dieser ID gefunden!'}
#             return render_template('reviewer/start.html',
#                                    form=form,
#                                    result=res)

#         sql = text(f"""
#         select
#         me.id, dat_fund_von, dat_fund_bis, dat_meld, dat_bear,
#         anzahl, fo_quelle, art_m, art_w, art_n, art_o, anm_melder,
#         anm_bearbeiter, be.beschreibung,
#         user_id,  user_name, user_rolle, user_kontakt,
#         plz, ort, strasse, land, kreis, amt, mtb,
#         longitude, latitude, ablage
#         from melduser mu
#         left join meldungen me on mu.id_meldung = me.id
#         left join users us on mu.id_user = us.id
#         left join fundorte fo on me.fo_zuordnung = fo.id
#         left join beschreibung be on fo.beschreibung = be.id
#         where me.id = {id};
#         """)

#         with db.engine.connect() as conn:
#             result = conn.execute(sql)
#             for row in result:
#                 row = row._mapping
#                 res = dict((name, val) for name, val in row.items())
#     form = ReviewerForm(formdata=MultiDict(res))
#     return render_template('reviewer/start.html', form=form, result=res)
