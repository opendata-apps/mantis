from flask import jsonify, render_template, request, Blueprint, send_from_directory
from app import db
# from app.database.models import Mantis
import json
from app.database.models import TblMeldungen, TblFundortBeschreibung, TblFundorte, TblMeldungUser, TblPlzOrt, TblUsers
from datetime import datetime
from app.forms import MantisSightingForm
from sqlalchemy import or_
from flask import render_template_string
from sqlalchemy import inspect, text
from sqlalchemy.orm import sessionmaker
import csv
from flask import Response, redirect, url_for
from io import StringIO, BytesIO
import os


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
    return render_template('admin/admin.html', reported_sightings=reported_sightings, tables=tables)


@admin.route('/toggle_approve_sighting/<id>', methods=['POST'])
def toggle_approve_sighting(id):
    # Find the report by id
    sighting = TblMeldungen.query.get(id)
    if sighting:
        # Toggle the 'approved' status
        sighting.approved = not sighting.approved
        db.session.commit()
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Report not found'}), 404


@admin.route('/get_sighting/<id>', methods=['GET'])
def get_sighting(id):
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
        return jsonify(sighting_dict)
    else:
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


@admin.route('/change_mantis_gender/<id>', methods=['POST'])
def change_mantis_gender(id):
    # Find the report by id
    sighting = TblMeldungen.query.get(id)
    if sighting:
        # Get the new gender from the request
        new_gender = request.form.get('new_gender')

        # Set the appropriate gender field to true and the rest to false
        sighting.art_m = new_gender == 'M'
        sighting.art_w = new_gender == 'W'
        sighting.art_n = new_gender == 'N'
        sighting.art_o = new_gender == 'O'

        db.session.commit()
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Report not found'}), 404


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


@admin.route('/admin/export/csv/reported_sightings')
def export_sightings():
    # Get the table object from the database
    table = TblMeldungen.__table__

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
