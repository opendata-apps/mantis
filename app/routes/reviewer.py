from flask import jsonify, render_template, request, Blueprint
from app import db
from datetime import datetime
from flask import render_template_string
from sqlalchemy import text
import csv
from flask import Response
from app.routes.reviewer_form import ReviewerForm
from werkzeug.datastructures import MultiDict

# Blueprints
review = Blueprint('reviewer', __name__)

@review.route('/reviewer')
@review.route('/reviewer', methods=['POST'])
def review_index():
    res = {'Anmerkung': 'Keinen Datensatz mit dieser ID gefunden!'}
    if request.method == 'POST': #and request.form['id']:
        try:
            id = int(request.form['id'])
        except:
            res = {'Anmerkung': 'Keinen Datensatz mit dieser ID gefunden!'}
            return render_template('reviewer/start.html', result=res)
            
        sql= text(f"""
        select
        me.id, dat_fund_von, dat_fund_bis, dat_meld, dat_bear,
        anzahl, fo_quelle, art_m, art_w, art_n, art_o, anm_melder, anm_bearbeiter,
        be.beschreibung,
        user_id,  user_name, user_rolle, user_kontakt,
        plz, ort, strasse, land, kreis, amt, mtb, longitude, latitude, ablage
        
        from melduser mu
        left join meldungen me on mu.id_meldung = me.id
        left join users us on mu.id_user = us.id
        left join fundorte fo on me.fo_zuordnung = fo.id
        left join beschreibung be on fo.beschreibung = be.id
        where me.id = {id};
        
        """)
        
        with db.engine.connect() as conn:
            result = conn.execute(sql)
            for row in result:
                row = row._mapping
                name_map = {'id': 'Datensatz',
                            'dat_fund_von': 'Funddatum vom',
                            'dat_fund_bis': 'Funddatum bis',
                            'dat_meld': 'Meldedatum',
                            'dat_bear': 'Datum der Bearbeitung',
                            'anzahl': 'Anzahl',
                            'fo_quelle': 'Fundort [Quelle]',
                            'art_m': 'Anzahl: Männchen',
                            'art_w': 'Anzahl: Weibchen',
                            'art_n': 'Anzahl: Nymphe',
                            'art_o': 'Anzahl: Oothek',
                            'anm_melder': 'Anmerkung [Melder]',
                            'anm_bearbeiter': 'Anmerkung [Bearbeiter]',
                            'beschreibung': 'Beschreigung [Fund und Ort]',
                            'user_id': 'Benutzerkennung',
                            'user_name': 'Benutername',
                            'user_rolle': 'Rolle',
                            'user_kontakt': 'Kontakt',
                            'plz': 'PLZ',
                            'ort': 'Ort',
                            'strasse': 'Strasse',
                            'land': 'Land',
                            'kreis': 'Kreis',
                            'amt': 'Amt',
                            'mtb': 'Messtischblatt',
                            'longitude': 'Länge',
                            'latitude': 'Breite',
                            'ablage': 'Pfad zum Bild'       
                            }
                
                res = dict((name, val) for name, val in row.items())
            print(res, type(res))
    form =  ReviewerForm(formdata=MultiDict(res))
    return render_template('reviewer/start.html', form=form, result=res)
