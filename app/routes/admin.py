import csv
from datetime import datetime, timedelta
from functools import wraps
from io import BytesIO, StringIO

import pandas as pd
from app import db
from app.config import Config
from app.database.full_text_search import FullTextSearch
from app.database.models import (TblFundortBeschreibung, TblFundorte,
                                 TblMeldungen, TblMeldungUser, TblUsers)
from flask import session
from flask import (Blueprint, Response, abort, flash, jsonify, redirect,
                   render_template, request, send_file, send_from_directory,
                   url_for)
from sqlalchemy import inspect, or_, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from app.tools.check_reviewer import login_required
import shutil
from werkzeug.utils import secure_filename
from pathlib import Path
from flask import current_app
from app.tools.send_reviewer_email import send_email

# Blueprints
admin = Blueprint('admin', __name__)


@admin.route('/reviewer/<usrid>')
def reviewer(usrid):
    # Fetch the user based on the 'usrid' parameter
    user = TblUsers.query.filter_by(user_id=usrid).first()

    # If the user doesn't exist or the role isn't 9, return 404
    if not user or user.user_rolle != '9':
        abort(403)

    now = datetime.utcnow()
    # Get the user_name of the logged in user_id
    user_name = user.user_name
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 21, type=int)
    last_updated = session.get('last_updated')
    # Store the userid in session
    session['user_id'] = usrid

    # Convert last_updated to a timezone-naive datetime if it's timezone-aware
    if last_updated and last_updated.tzinfo:
        last_updated = last_updated.replace(tzinfo=None)

    if last_updated is None or now - last_updated > timedelta(minutes=1):
        FullTextSearch.refresh_materialized_view()
        session['last_updated'] = now

    filter_status = request.args.get('statusInput', 'offen')
    filter_type = request.args.get('typeInput', None)
    sort_order = request.args.get('sort_order', 'id_asc')
    search_query = request.args.get('q', None)
    search_type = request.args.get('search_type', 'full_text')
    date_from = request.args.get('dateFrom', None)
    date_to = request.args.get('dateTo', None)

    image_path = Config.UPLOAD_FOLDER.replace("app/", "")
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    if 'statusInput' not in request.args and 'sort_order' not in request.args:
        return redirect(url_for('admin.reviewer',
                                usrid=usrid,
                                statusInput='offen',
                                sort_order='id_asc'))

    query = TblMeldungen.query

    # Apply filter conditions based on 'filter_status'
    if filter_status == 'bearbeitet':
        query = query.filter(TblMeldungen.dat_bear.isnot(None), or_(
            TblMeldungen.deleted.is_(None),
            TblMeldungen.deleted == False))
    elif filter_status == 'offen':
        query = query.filter(TblMeldungen.dat_bear.is_(None), or_(
            TblMeldungen.deleted.is_(None),
            TblMeldungen.deleted == False))
    elif filter_status == 'geloescht':
        query = query.filter(TblMeldungen.deleted == True)
    elif filter_status == 'all':
        # If the filter is set to 'all',
        # include both deleted and non-deleted items
        query = query.filter(or_(TblMeldungen.deleted.is_(None),
                                 TblMeldungen.deleted == False,
                                 TblMeldungen.deleted == True))
    elif search_query:
        # If there's a search query,
        # don't apply any deletion filter
        pass
    else:
        # Default behavior: Exclude deleted items
        query = query.filter(or_(TblMeldungen.deleted.is_(
            None), TblMeldungen.deleted == False))

    if filter_type:
        if filter_type == 'maennlich':
            query = query.filter(TblMeldungen.art_m >= 1)
        elif filter_type == 'weiblich':
            query = query.filter(TblMeldungen.art_w >= 1)
        elif filter_type == 'oothek':
            query = query.filter(TblMeldungen.art_o >= 1)
        elif filter_type == 'nymhe':
            query = query.filter(TblMeldungen.art_n >= 1)
        elif filter_type == 'andere':
            query = query.filter(TblMeldungen.art_f >= 1)
        elif filter_type == 'nicht_bestimmt':
            query = query.filter(TblMeldungen.art_m.is_(None),
                                 TblMeldungen.art_w.is_(None),
                                 TblMeldungen.art_o.is_(None),
                                 TblMeldungen.art_n.is_(None),
                                 TblMeldungen.art_f.is_(None))

    # Apply sort order
    if sort_order == 'id_asc':
        query = query.order_by(TblMeldungen.id.asc())
    elif sort_order == 'id_desc':
        query = query.order_by(TblMeldungen.id.desc())

    # Apply full-text search if there's a search query
    if search_query:
        try:
            if search_type == 'id':
                try:
                    search_query = int(search_query)
                    query = query.filter(TblMeldungen.id == search_query)
                except ValueError:
                    search_type = 'full_text'

            if search_type == 'full_text':
                if "@" in search_query:
                    query = query.join(TblMeldungUser,
                                       TblMeldungen.id == TblMeldungUser.id_meldung)\
                        .join(TblUsers, TblMeldungUser.id_user == TblUsers.id)\
                        .filter(TblUsers.user_kontakt.ilike(f"%{search_query}%"))
                else:
                    # Option 1: Sanitize the query string
                    search_query = search_query.replace(' ', ' & ')
                    search_vector = text("plainto_tsquery('german', :query)").bindparams(
                        # Option 2: Use plainto_tsquery
                        query=f"{search_query}")
                    search_results = FullTextSearch.query.filter(
                        FullTextSearch.doc.op('@@')(search_vector)
                    ).all()
                    reported_sightings_ids = [
                        result.meldungen_id for result in search_results]
                    query = query.filter(
                        TblMeldungen.id.in_(reported_sightings_ids))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash('An internal error occurred. Please try again.',
                  'error')
        except Exception as e:
            db.session.rollback()
            flash('Your search could not be completed. Please try again.',
                  'error')

    if date_from and date_to:
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
        query = query.filter(TblMeldungen.dat_fund_von.between(
            date_from_obj, date_to_obj))
    elif date_from:
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        query = query.filter(TblMeldungen.dat_fund_von >= date_from_obj)
    elif date_to:
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
        query = query.filter(TblMeldungen.dat_fund_von <= date_to_obj)

    paginated_sightings = query.paginate(
        page=page, per_page=per_page, error_out=False)

    reported_sightings = paginated_sightings.items
    for sighting in reported_sightings:
        sighting.fundort = TblFundorte.query.get(sighting.fo_zuordnung)
        sighting.beschreibung = TblFundortBeschreibung.query.get(
            sighting.fundort.beschreibung)
        sighting.ort = sighting.fundort.ort
        sighting.plz = sighting.fundort.plz
        sighting.kreis = sighting.fundort.kreis
        sighting.land = sighting.fundort.land
        sighting.deleted = sighting.deleted
        sighting.dat_bear = sighting.dat_bear
        if sighting.bearb_id:
            approver = TblUsers.query.filter_by(
                user_id=sighting.bearb_id).first()
            sighting.approver_username = approver.user_name if approver else 'Unknown'
    return render_template('admin/admin.html',
                           user_id=usrid,
                           paginated_sightings=paginated_sightings,
                           reported_sightings=reported_sightings,
                           tables=tables,
                           image_path=image_path,
                           user_name=user_name,
                           filters={"status": filter_status,
                                    "type": filter_type},
                           current_filter_status=filter_status,
                           current_sort_order=sort_order,
                           search_query=search_query,
                           search_type=search_type)


@admin.route("/change_mantis_meta_data/<int:id>", methods=["POST"])
@login_required
def change_mantis_meta_data(id):
    # Find the report by id
    new_data = request.form.get('new_data')
    fieldname = request.form.get('type')
    if fieldname in ['fo_quelle', 'anm_bearbeiter']:
        sighting = TblMeldungen.query.get(id)
    else:
        fo_id = TblMeldungen.query.get(id).fo_zuordnung
        sighting = TblFundorte.query.get(fo_id)
    if sighting:
        # Update sighting with data from request
        # This will depend on how you implement
        # the saveChanges function in JavaScript
        # sighting.field = request.form['field']
        sighting.bearb_id = session['user_id']
        if fieldname == 'fo_quelle':
            sighting.fo_quelle = new_data
        elif fieldname == 'anm_bearbeiter':
            sighting.anm_bearbeiter = new_data
        elif fieldname == 'amt':
            sighting.amt = new_data
        elif fieldname == 'mtb':
            sighting.mtb = new_data
        elif fieldname == 'latitude':
            sighting.latitude = new_data
        elif fieldname == 'longitude':
            sighting.longitude = new_data
        db.session.commit()
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Report not found'}), 404


@admin.route('/<path:filename>')
def report_Img(filename):
    return send_from_directory('',
                               filename, mimetype='image/webp',
                               as_attachment=False)


@admin.route('/toggle_approve_sighting/<id>', methods=['POST'])
@login_required
def toggle_approve_sighting(id):
    "Find ID and mark as edited with a date in column dat_bear"

    # Find the report by id
    sighting = TblMeldungen.query.get(id)
    if sighting:
        # Set the dat_bear value to the current
        # datetime if it is not already set
        if not sighting.dat_bear:
            sighting.dat_bear = datetime.now()
        else:
            # Clear the dat_bear value if it is already set
            sighting.dat_bear = None
        sighting.bearb_id = session['user_id']
        db.session.commit()
    if Config.send_emails:
        # get data for E-Mail if send_email is True      
        sighting = db.session.query(
            TblMeldungen,
            TblFundorte,
            TblFundortBeschreibung,
            TblMeldungUser,
            TblUsers
        ).join(
            TblFundorte,
            TblMeldungen.fo_zuordnung == TblFundorte.id
        ).join(
            TblFundortBeschreibung,
            TblFundorte.beschreibung == TblFundortBeschreibung.id
        ).join(
            TblMeldungUser,
            TblMeldungen.id == TblMeldungUser.id_meldung
        ).join(
            TblUsers,
            TblMeldungUser.id_user == TblUsers.id
        ).filter(
            TblMeldungen.id == id
        ).first()
        
        if sighting:
            dbdata = {}
            for part in sighting:
                part_dict = {c.name: getattr(part, c.name)
                             for c in part.__table__.columns}
                dbdata.update(part_dict)

            if dbdata['user_kontakt']:
                send_email(dbdata)
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Report not found'}), 404


@admin.route('/get_sighting/<id>', methods=['GET', 'POST'])
@login_required
def get_sighting(id):
    # Find the report by id
    sighting = db.session.query(
        TblMeldungen,
        TblFundorte,
        TblFundortBeschreibung,
        TblMeldungUser,
        TblUsers
    ).join(
        TblFundorte,
        TblMeldungen.fo_zuordnung == TblFundorte.id
    ).join(
        TblFundortBeschreibung,
        TblFundorte.beschreibung == TblFundortBeschreibung.id
    ).join(
        TblMeldungUser,
        TblMeldungen.id == TblMeldungUser.id_meldung
    ).join(
        TblUsers,
        TblMeldungUser.id_user == TblUsers.id
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


@admin.route('/delete_sighting/<id>', methods=['POST'])
@login_required
def delete_sighting(id):
    # Find the report by id
    sighting = TblMeldungen.query.get(id)
    if sighting:
        # Set the deleted value to True
        sighting.deleted = True
        sighting.bearb_id = session['user_id']
        db.session.commit()
        return jsonify({'message': 'Report successfully deleted'}), 200
    else:
        return jsonify({'error': 'Report not found'}), 404


@admin.route('/save_sighting_changes/<id>', methods=['POST'])
@login_required
def save_sighting_changes(id):
    # Find the report by id

    sighting = TblMeldungen.query.get(id)
    if sighting:
        # Update sighting with data from request
        # This will depend on how you implement
        # the saveChanges function in JavaScript
        # sighting.field = request.form['field']
        sighting = session['user_id']
        db.session.commit()
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Report not found'}), 404


@admin.route("/change_mantis_gender/<int:id>", methods=["POST"])
@login_required
def change_gender(id):
    new_gender = request.form.get('new_gender')

    sighting = TblMeldungen.query.get(id)

    # Reset all gender columns to 0
    sighting.art_m = 0
    sighting.art_w = 0
    sighting.art_n = 0
    sighting.art_o = 0
    sighting.art_f = 0

    # Update the specified gender to 1
    if new_gender == 'M':
        sighting.art_m = 1
    elif new_gender == 'W':
        sighting.art_w = 1
    elif new_gender == 'N':
        sighting.art_n = 1
    elif new_gender == 'O':
        sighting.art_o = 1
    elif new_gender == 'F':
        sighting.art_f = 1

    sighting.bearb_id = session['user_id']
    db.session.commit()

    return jsonify(success=True)


@admin.route("/change_mantis_count/<int:id>", methods=["POST"])
@login_required
def change_mantis_count(id):
    new_count = request.form.get('new_count')
    mantis_type = request.form.get('type')
    sighting = TblMeldungen.query.get(id)

    # Update the count for the specified mantis type
    if mantis_type == 'Männchen':
        sighting.art_m = new_count
    elif mantis_type == 'Weiblich':
        sighting.art_w = new_count
    elif mantis_type == 'Nymphe':
        sighting.art_n = new_count
    elif mantis_type == 'Oothek':
        sighting.art_o = new_count
    elif mantis_type == 'Andere':
        sighting.art_f = new_count
    elif mantis_type == 'Anzahl':
        sighting.tiere = new_count

    sighting.bearb_id = session['user_id']
    db.session.commit()

    return jsonify(success=True)



@admin.route('/admin/export/csv/<table_name>', methods=['GET'])
@login_required
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
    headers = {"Content-Disposition": "attachment; filename=data.csv"}
    return Response(si,
                    mimetype='text/csv',
                    headers=headers)


@admin.route('/adminPanel', methods=['GET'])
@login_required
def admin_panel():
    if 'user_id' in session:
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        tables = [table for table in tables if table != 'alembic_version']
        return render_template('admin/adminPanel.html',
                               tables=tables,
                               user_id=session['user_id'])
    else:
        return "Unauthorized", 403


NON_EDITABLE_FIELDS = {
  'meldungen': ['id', 'fo_zuordnung'],
  'beschreibung': ['id'],
  'fundorte': ['id', 'ablage', 'beschreibung'],
  'melduser': ['id', 'id_finder', 'id_meldung', 'id_user'],
  'users': ['id', 'user_id']
} 


@admin.route('/update_value/<table_name>/<row_id>', methods=['POST'])
@login_required
def update_value(table_name, row_id):
    data = request.json
    column_name = data.get("column_name")

    # Check if field is non-editable
    if column_name in NON_EDITABLE_FIELDS.get(table_name, []):
        return jsonify({'error': 'Field is non-editable'}), 400

    new_value = data.get("new_value")

    table = db.metadata.tables.get(table_name)
    if table is None:
        return jsonify({'error': 'Table not found'})

    # If the updated field is 'dat_meld', call the image update function
    if table_name == 'meldungen' and column_name == 'dat_meld':
        response, status = update_report_image_date(row_id, new_value)
        if status != 200:
            return jsonify(response), status

    # Assuming the primary key column is named 'id'
    stmt = table.update().where(table.c.id == row_id).values({column_name: new_value})
    db.session.execute(stmt)
    db.session.commit()

    return jsonify({'status': 'success'})


def update_report_image_date(report_id, new_date):
    new_date_obj = datetime.strptime(new_date, '%Y-%m-%d')

    # Fetch the report
    report = db.session.query(TblMeldungen).filter_by(id=report_id).first()
    if not report:
        return {'error': 'Report not found'}, 404

    # Fetch the corresponding fundorte record
    fundorte_record = db.session.query(
        TblFundorte).filter_by(id=report.fo_zuordnung).first()
    if not fundorte_record:
        return {'error': 'Fundorte record not found'}, 404

    base_dir = Path(current_app.config['UPLOAD_FOLDER'])
    old_image_path = base_dir / fundorte_record.ablage

    old_dir, old_filename = os.path.split(old_image_path)
    location, _, usrid = old_filename.rsplit('-', 2)

    old_dir, old_filename = os.path.split(old_image_path)
    location, _, usrid = old_filename.rsplit('-', 2)

    new_dir_path = _create_directory(new_date_obj)
    new_filename = _create_filename(location, usrid, new_date_obj)
    new_file_path = new_dir_path / (new_filename + ".webp")

    try:
        shutil.move(str(old_image_path), str(new_file_path))

        # Check if old directory is empty, if yes, delete it
        if not os.listdir(old_dir):
            os.rmdir(old_dir)

    except IOError as e:
        return {'error': f'Failed to move file: {e}'}, 500

    # Update the path in fundorte table
    fundorte_record.ablage = str(new_file_path.relative_to(base_dir))
    db.session.commit()

    return {'status': 'success'}, 200


def _create_directory(new_date):
    year = new_date.strftime("%Y")
    base_dir = Path(current_app.config['UPLOAD_FOLDER'])
    dir_path = base_dir / year / new_date.strftime('%Y-%m-%d')
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path



def _create_filename(location, usrid, new_date):
    new_timestamp = new_date.strftime("%Y%m%d%H%M%S")
    # Generate the filename without the .webp extension
    return '{}-{}-{}'.format(secure_filename(location),
                             new_timestamp,
                             secure_filename(usrid))


# Get all table names
@admin.route('/get_tables', methods=['GET'])
@login_required
def get_tables():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    tables = [table for table in tables if table != 'alembic_version']
    return jsonify({"tables": tables})


@admin.route('/table/<table_name>')
@login_required
def get_table_data(table_name):
    limit = 20
    offset = request.args.get('offset', default=0, type=int) # Get the offset parameter from the request
    table = db.metadata.tables.get(table_name)
    if table is None:
        return jsonify({'error': 'Table not found'})
    result = db.session.execute(table.select().order_by(table.c.id).limit(limit).offset(offset))  # Add limit and offset to the query
    column_names = result.keys()
    data = [{column: value for column, value in zip(column_names, row)} for row in result]
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
        TblFundorte,
        TblMeldungen.fo_zuordnung == TblFundorte.id
    ).join(
        TblFundortBeschreibung,
        TblFundorte.beschreibung == TblFundortBeschreibung.id
    ).join(
        TblMeldungUser,
        TblMeldungen.id == TblMeldungUser.id_meldung
    ).join(
        TblUsers,
        TblMeldungUser.id_user == TblUsers.id
    )
    

    return query.all()


@admin.route('/admin/export/xlsx/<string:value>')
@login_required
def export_data(value):
    current_time = datetime.now().strftime("%d.%m.%Y_%H%M")

    if value == 'all':
        data = perform_query()
        filename = f'Alle_Meldungen_{current_time}.xlsx'
    elif value == 'accepted':
        data = perform_query(filter_value=True)
        filename = f'Akzeptierte_Meldungen_{current_time}.xlsx'
    elif value == 'non_accepted':
        data = perform_query(filter_value=False)
        filename = f'Nicht_akzeptierte_Meldungen_{current_time}.xlsx'
    else:
        abort(404, description="Resource not found")

    data_dicts = [row2dict(row) for row in data]
    df = pd.DataFrame(data_dicts)

    # Write the DataFrame to an Excel file
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Daten', index=False)

    # Reset the file pointer to the beginning
    output.seek(0)

    # Send the file
    mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    return send_file(output,
                     mimetype=mime,
                     as_attachment=True, download_name=filename)
