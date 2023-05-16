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
from flask import Response
from io import StringIO


# Blueprints
admin = Blueprint('admin', __name__)


@admin.route('/admin')
@admin.route('/admin')
def admin_index():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    reported_sightings = TblMeldungen.query.all()
    return render_template('admin/adminPanel.html', reported_sightings=reported_sightings, tables=tables)


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
