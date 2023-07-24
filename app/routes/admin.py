from flask import jsonify, render_template, request, Blueprint, send_from_directory
from app import db
# from app.database.models import Mantis
import json
from app.database.models import TblMeldungen, TblFundortBeschreibung, TblFundorte, TblMeldungUser, TblPlzOrt, TblUsers
from datetime import datetime
from app.forms import MantisSightingForm
from sqlalchemy import or_, MetaData
from flask import render_template_string
from sqlalchemy import inspect, text
from sqlalchemy.orm import sessionmaker, joinedload
import csv
from flask import Response, redirect, url_for
from io import StringIO, BytesIO
import os
import pandas as pd
from io import BytesIO
from flask import send_file
from sqlalchemy import Table, create_engine
from flask import abort

# Blueprints
admin = Blueprint('admin', __name__)


@admin.route('/adminPanel')
def admin_index():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    reported_sightings = TblMeldungen.query.all()
    return render_template('admin/adminPanel.html', reported_sightings=reported_sightings, tables=tables)


@admin.route('/admin')
def admin_index2():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    reported_sightings = TblMeldungen.query.all()
    for sighting in reported_sightings:
        sighting.fundort = TblFundorte.query.get(sighting.fo_zuordnung)
        sighting.beschreibung = TblFundortBeschreibung.query.get(
            sighting.fundort.beschreibung)
        sighting.ort = sighting.fundort.ort
        sighting.plz = sighting.fundort.plz
        sighting.kreis = sighting.fundort.kreis
        sighting.land = sighting.fundort.land
    return render_template('admin/admin.html', reported_sightings=reported_sightings, tables=tables)


@admin.route('/<path:filename>')
def report_Img(filename):
    print("Get image with filename: " + filename + "")
    return send_from_directory('', filename)


@admin.route('/toggle_approve_sighting/<id>', methods=['POST'])
def toggle_approve_sighting(id):
    # Find the report by id
    sighting = TblMeldungen.query.get(id)
    if sighting:
        # Set the dat_bear value to the current datetime if it is not already set
        if not sighting.dat_bear:
            sighting.dat_bear = datetime.now()
        else:
            sighting.dat_bear = None  # Clear the dat_bear value if it is already set

        db.session.commit()
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Report not found'}), 404


@admin.route('/get_sighting/<id>', methods=['GET'])
def get_sighting(id):
    print("Get sighting with id: " + id + "")
    # Find the report by id
    sighting = db.session.query(
        TblMeldungen,
        TblFundorte,
        TblFundortBeschreibung,
        TblMeldungUser,
        TblUsers
    ).join(
        TblFundorte, TblMeldungen.fo_zuordnung == TblFundorte.id
    ).join(
        TblFundortBeschreibung, TblFundorte.beschreibung == TblFundortBeschreibung.id
    ).join(
        TblMeldungUser, TblMeldungen.id == TblMeldungUser.id_meldung
    ).join(
        TblUsers, TblMeldungUser.id_user == TblUsers.id
    ).filter(
        TblMeldungen.id == id
    ).first()

    if sighting:
        # Convert sighting to a dictionary and return it
        sighting_dict = {}
        for part in sighting:
            part_dict = {c.name: getattr(part, c.name)
                         for c in part.__table__.columns}
            sighting_dict.update(part_dict)
        print(sighting_dict)
        return jsonify(sighting_dict)
    else:
        print(jsonify({'error': 'Report not found'}), 404)
        return jsonify({'error': 'Report not found'}), 404


@admin.route('/delete_sighting/<id>', methods=['GET'])
def delete_sighting(id):
    # Find the report by id
    sighting = TblMeldungen.query.get(id)
    if sighting:
        # Delete the report
        db.session.delete(sighting)
        db.session.commit()
        # Redirect back to admin dashboard
        return redirect(url_for('admin_index'))
    else:
        return jsonify({'error': 'Report not found'}), 404


@admin.route('/save_sighting_changes/<id>', methods=['POST'])
def save_sighting_changes(id):
    # Find the report by id
    sighting = TblMeldungen.query.get(id)
    if sighting:
        # Update sighting with data from request
        # This will depend on how you implement the saveChanges function in JavaScript
        # sighting.field = request.form['field']
        db.session.commit()
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Report not found'}), 404


@admin.route("/change_mantis_gender/<int:id>", methods=["POST"])
def change_gender(id):
    new_gender = request.form.get('new_gender')

    sighting = TblMeldungen.query.get(id)

    # Reset all gender columns to 0
    sighting.art_m = 0
    sighting.art_w = 0
    sighting.art_n = 0
    sighting.art_o = 0
    sighting.art_s = 0

    # Update the specified gender to 1
    if new_gender == 'M':
        sighting.art_m = 1
    elif new_gender == 'W':
        sighting.art_w = 1
    elif new_gender == 'N':
        sighting.art_n = 1
    elif new_gender == 'O':
        sighting.art_o = 1
    elif new_gender == 'S':
        sighting.art_s = 1

    db.session.commit()

    return jsonify(success=True)


@admin.route("/change_mantis_count/<int:id>", methods=["POST"])
def change_mantis_count(id):
    new_count = request.form.get('new_count')
    mantis_type = request.form.get('type')

    sighting = TblMeldungen.query.get(id)

    # Update the count for the specified mantis type
    if mantis_type == 'Männlich':
        sighting.art_m = new_count
    elif mantis_type == 'Weiblich':
        sighting.art_w = new_count
    elif mantis_type == 'Nymphe':
        sighting.art_n = new_count
    elif mantis_type == 'Ootheke':
        sighting.art_o = new_count
    elif mantis_type == 'Andere':
        sighting.art_s = new_count

    db.session.commit()

    print(
        f"Changed count of {mantis_type} to {new_count} for sighting with id {id} now {sighting.art_m} {sighting.art_w} {sighting.art_n} {sighting.art_o} {sighting.art_s}")

    return jsonify(success=True)


@admin.route('/admin/log')
def admin_subsites_log():
    return render_template('admin/log.html')


@admin.route('/admin/userAdministration')
def admin_subsites_users():
    return render_template('admin/userAdministration.html')


@admin.route('/admin/export/csv/<table_name>', methods=['GET'])
def export_csv(table_name):
    # Get the table object from the database
    table = db.metadata.tables.get(table_name)

    if table is None:
        return jsonify({'error': 'Table not found'})

    # Execute a select statement on the table
    result = db.session.execute(table.select())

    # Get the names of the columns
    column_names = result.keys()

    # Create an in-memory text stream
    si = StringIO()

    # Create a CSV writer
    writer = csv.writer(si)

    # Write column names
    writer.writerow(column_names)

    # Write data rows
    for row in result:
        writer.writerow(row)

    # Set the position of the stream to the beginning
    si.seek(0)

    # Return the CSV data as a response
    return Response(si, mimetype='text/csv', headers={"Content-Disposition": "attachment; filename=data.csv"})


# Get all table names
@admin.route('/get_tables', methods=['GET'])
def get_tables():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(jsonify({"tables": tables}))
    return jsonify({"tables": tables})


@admin.route('/table/<table_name>')
def get_table_data(table_name):
    # Get the table object from the database
    table = db.metadata.tables.get(table_name)

    if table is None:
        return jsonify({'error': 'Table not found'})

    # Execute a select statement on the table
    result = db.session.execute(table.select())

    # Get the names of the columns
    column_names = result.keys()

    # Serialize the result as a JSON object
    data = [{column: value for column, value in zip(
        column_names, row)} for row in result]
    return jsonify(data)


# Define a function to convert a row to a dictionary
def row2dict(row):
    d = {}
    for item in row:
        for column in item.__table__.columns:
            d[column.name] = str(getattr(item, column.name))

    return d

# Function to perform the query


def perform_query(filter_value=None):
    # Create a session
    Session = sessionmaker(bind=db.engine)
    session = Session()

    query = session.query(
        TblMeldungen,
        TblFundorte,
        TblFundortBeschreibung,
        TblMeldungUser,
        TblUsers
    ).join(
        TblFundorte, TblMeldungen.fo_zuordnung == TblFundorte.id
    ).join(
        TblFundortBeschreibung, TblFundorte.beschreibung == TblFundortBeschreibung.id
    ).join(
        TblMeldungUser, TblMeldungen.id == TblMeldungUser.id_meldung
    ).join(
        TblUsers, TblMeldungUser.id_user == TblUsers.id
    )

    # Apply the filter if necessary
    if filter_value is not None:
        if filter_value:
            # rows where dat_bear is not null
            query = query.filter(TblMeldungen.dat_bear.isnot(None))
        else:
            # rows where dat_bear is null
            query = query.filter(TblMeldungen.dat_bear.is_(None))

    return query.all()

# Route


@admin.route('/admin/export/xlsx/<string:value>')
def export_data(value):
    if value == 'all':
        data = perform_query()
        filename = 'all_data.xlsx'
    elif value == 'accepted':
        data = perform_query(filter_value=True)
        filename = 'accepted_reports.xlsx'
    elif value == 'non_accepted':
        data = perform_query(filter_value=False)
        filename = 'non_accepted_reports.xlsx'
    else:
        abort(404, description="Resource not found")

    data_dicts = [row2dict(row) for row in data]
    df = pd.DataFrame(data_dicts)

    # Write the DataFrame to an Excel file
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Data', index=False)

    # Reset the file pointer to the beginning
    output.seek(0)

    # Send the file
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=filename)
