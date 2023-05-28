from flask import jsonify, render_template, request, Blueprint, send_from_directory
from app import db
# from app.database.models import Mantis
import json
from app.database.models import TblMeldungen, TblFundortBeschreibung, TblFundorte, TblMeldungUser, TblPlzOrt, TblUsers
from datetime import datetime
from app.forms import MantisSightingForm
from sqlalchemy import or_

# Blueprints
data = Blueprint('data', __name__)



# Flask application and routes
@data.route('/report', methods=['GET', 'POST'])
def report():
    form = MantisSightingForm()
    if form.validate_on_submit():
        # Save form data to the database
        pass  # Implement the logic to save the data
    return render_template('report.html', form=form)


@data.route('/autocomplete', methods=['GET'])
def autocomplete():
    query = request.args.get('q')
    results = db.session.query(TblPlzOrt).filter(
        or_(
            TblPlzOrt.plz.startswith(query),
            TblPlzOrt.ort.startswith(query),
            TblPlzOrt.landkreis.startswith(query),
            TblPlzOrt.bundesland.startswith(query)
        )
    ).limit(10).all()

    suggestions = []
    for result in results:
        suggestions.append({
            'plz': result.plz,
            'ort': result.ort,
            'landkreis': result.landkreis,
            'bundesland': result.bundesland
        })

    return jsonify(suggestions)


@data.route('/auswertungen')
def show_map():
    # Fetch the reports data from the database
    reports = TblFundorte.query.join(
        TblMeldungen, TblMeldungen.fo_zuordnung == TblFundorte.id).all()
    # Serialize the reports data as a JSON object
    reportsJson = json.dumps(
        [{'latitude': report.latitude.replace(',','.'),
          'longitude': report.longitude.replace(',','.')}
         for report in reports])
    # Render the template with the serialized data
    return render_template('map.html', reportsJson=reportsJson)


@data.route('/statistics')
def statistics():
    mantis_count = TblMeldungen.query.count()
    return render_template('statistics.html', mantis_count=mantis_count)
