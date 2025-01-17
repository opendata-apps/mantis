import csv
from datetime import datetime, timedelta
from functools import wraps
from io import BytesIO, StringIO
import pandas as pd
from app import db
from app.config import Config
from app.database.full_text_search import FullTextSearch
from app.database.models import (
    TblFundortBeschreibung,
    TblFundorte,
    TblMeldungen,
    TblMeldungUser,
    TblUsers,
    TblAllData
)
from flask import session
from flask import (
    Blueprint,
    Response,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    url_for,
)
from sqlalchemy import inspect, or_, text, cast, String, update
from sqlalchemy.sql import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, Session, load_only
from app.tools.check_reviewer import login_required
import shutil
from werkzeug.utils import secure_filename
from pathlib import Path
from flask import current_app
from app.tools.send_reviewer_email import send_email

import os

# Blueprints
admin = Blueprint("admin", __name__)

# Add this constant at the top of the file
NON_EDITABLE_FIELDS = {
    "meldungen": ["id", "fo_zuordnung"],
    "beschreibung": ["id"],
    "fundorte": ["id", "ablage", "beschreibung"],
    "melduser": ["id", "id_finder", "id_meldung", "id_user"],
    "users": ["id", "user_id"],
    "all_data_view": ["id", "id_meldung", "fo_zuordnung", "report_user_db_id", "fundorte_id", "beschreibung_id", "dat_fund_von", "ort", "report_user_id"]
}


@admin.route("/reviewer/<usrid>")
def reviewer(usrid):
    "This function is used to display the reviewer page"
    # Fetch the user based on the 'usrid' parameter
    user = TblUsers.query.filter_by(user_id=usrid).first()

    # If the user doesn't exist or the role isn't 9, return 404
    if not user or user.user_rolle != "9":
        abort(403)

    now = datetime.utcnow()
    # Get the user_name of the logged in user_id
    user_name = user.user_name
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 21, type=int)
    last_updated = session.get("last_updated")
    # Store the userid in session
    session["user_id"] = usrid

    # Convert last_updated to a timezone-naive datetime if it's timezone-aware
    if last_updated and last_updated.tzinfo:
        last_updated = last_updated.replace(tzinfo=None)

    if last_updated is None or now - last_updated > timedelta(minutes=1):
        FullTextSearch.refresh_materialized_view()
        session["last_updated"] = now

    filter_status = request.args.get("statusInput", "offen")
    filter_type = request.args.get("typeInput", None)
    sort_order = request.args.get("sort_order", "id_asc")
    search_query = request.args.get("q", None)
    search_type = request.args.get("search_type", "full_text")
    date_from = request.args.get("dateFrom", None)
    date_to = request.args.get("dateTo", None)

    image_path = Config.UPLOAD_FOLDER.replace("app/", "")
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    if "statusInput" not in request.args and "sort_order" not in request.args:
        return redirect(
            url_for(
                "admin.reviewer", usrid=usrid, statusInput="offen", sort_order="id_asc"
            )
        )

    query = TblMeldungen.query

    # Apply filter conditions based on 'filter_status'
    if filter_status == "bearbeitet":
        query = query.filter(
            TblMeldungen.dat_bear.isnot(None),
            or_(TblMeldungen.deleted.is_(None), TblMeldungen.deleted == False),
        )
    elif filter_status == "offen":
        query = query.filter(
            TblMeldungen.dat_bear.is_(None),
            or_(TblMeldungen.deleted.is_(None), TblMeldungen.deleted == False),
        )
    elif filter_status == "geloescht":
        query = query.filter(TblMeldungen.deleted == True)
    elif filter_status == "all":
        # If the filter is set to 'all',
        # include both deleted and non-deleted items
        query = query.filter(
            or_(
                TblMeldungen.deleted.is_(None),
                TblMeldungen.deleted == False,
                TblMeldungen.deleted == True,
            )
        )
    elif search_query:
        # If there's a search query,
        # don't apply any deletion filter
        pass
    else:
        # Default behavior: Exclude deleted items
        query = query.filter(
            or_(TblMeldungen.deleted.is_(None), TblMeldungen.deleted == False)
        )

    if filter_type:
        if filter_type == "maennlich":
            query = query.filter(TblMeldungen.art_m >= 1)
        elif filter_type == "weiblich":
            query = query.filter(TblMeldungen.art_w >= 1)
        elif filter_type == "oothek":
            query = query.filter(TblMeldungen.art_o >= 1)
        elif filter_type == "Nymphe":
            query = query.filter(TblMeldungen.art_n >= 1)
        elif filter_type == "andere":
            query = query.filter(TblMeldungen.art_f >= 1)
        elif filter_type == "nicht_bestimmt":
            query = query.filter(
                TblMeldungen.art_m.is_(None),
                TblMeldungen.art_w.is_(None),
                TblMeldungen.art_o.is_(None),
                TblMeldungen.art_n.is_(None),
                TblMeldungen.art_f.is_(None),
            )

    # Apply sort order
    if sort_order == "id_asc":
        query = query.order_by(TblMeldungen.id.asc())
    elif sort_order == "id_desc":
        query = query.order_by(TblMeldungen.id.desc())

    # Apply full-text search if there's a search query
    if search_query:
        try:
            if search_type == "id":
                try:
                    search_query = int(search_query)
                    query = query.filter(TblMeldungen.id == search_query)
                except ValueError:
                    search_type = "full_text"

            if search_type == "full_text":
                if "@" in search_query:
                    query = (
                        query.join(
                            TblMeldungUser, TblMeldungen.id == TblMeldungUser.id_meldung
                        )
                        .join(TblUsers, TblMeldungUser.id_user == TblUsers.id)
                        .filter(TblUsers.user_kontakt.ilike(f"%{search_query}%"))
                    )
                else:
                    # Option 1: Sanitize the query string
                    search_query = search_query.replace(" ", " & ")
                    search_vector = text(
                        "plainto_tsquery('german', :query)"
                    ).bindparams(
                        # Option 2: Use plainto_tsquery
                        query=f"{search_query}"
                    )
                    search_results = FullTextSearch.query.filter(
                        FullTextSearch.doc.op("@@")(search_vector)
                    ).all()
                    reported_sightings_ids = [
                        result.meldungen_id for result in search_results
                    ]
                    query = query.filter(TblMeldungen.id.in_(reported_sightings_ids))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash("An internal error occurred. Please try again.", "error")
            print(e)
        except Exception as e:
            db.session.rollback()
            flash("Your search could not be completed. Please try again.", "error")
            print(e)

    if date_from and date_to:
        date_from_obj = datetime.strptime(date_from, "%d.%m.%Y")
        date_to_obj = datetime.strptime(date_to, "%d.%m.%Y")
        query = query.filter(
            TblMeldungen.dat_fund_von.between(date_from_obj, date_to_obj)
        )
    elif date_from:
        date_from_obj = datetime.strptime(date_from, "%d.%m.%Y")
        query = query.filter(TblMeldungen.dat_fund_von >= date_from_obj)
    elif date_to:
        date_to_obj = datetime.strptime(date_to, "%d.%m.%Y")
        query = query.filter(TblMeldungen.dat_fund_von <= date_to_obj)

    paginated_sightings = query.paginate(page=page, per_page=per_page, error_out=False)

    reported_sightings = paginated_sightings.items
    for sighting in reported_sightings:
        sighting.fundort = TblFundorte.query.get(sighting.fo_zuordnung)
        sighting.beschreibung = TblFundortBeschreibung.query.get(
            sighting.fundort.beschreibung
        )
        sighting.ort = sighting.fundort.ort
        sighting.plz = sighting.fundort.plz
        sighting.kreis = sighting.fundort.kreis
        sighting.land = sighting.fundort.land
        sighting.deleted = sighting.deleted
        sighting.dat_bear = sighting.dat_bear
        if sighting.bearb_id:
            approver = TblUsers.query.filter_by(user_id=sighting.bearb_id).first()
            sighting.approver_username = approver.user_name if approver else "Unknown"
    return render_template(
        "admin/admin.html",
        user_id=usrid,
        paginated_sightings=paginated_sightings,
        reported_sightings=reported_sightings,
        tables=tables,
        image_path=image_path,
        user_name=user_name,
        filters={"status": filter_status, "type": filter_type},
        current_filter_status=filter_status,
        current_sort_order=sort_order,
        search_query=search_query,
        search_type=search_type,
    )


@admin.route("/change_mantis_meta_data/<int:id>", methods=["POST"])
@login_required
def change_mantis_meta_data(id):
    "Change mantis report metadata"
    # Find the report by id
    new_data = request.form.get("new_data")
    fieldname = request.form.get("type")
    if fieldname in ["fo_quelle", "anm_bearbeiter"]:
        sighting = TblMeldungen.query.get(id)
    else:
        fo_id = TblMeldungen.query.get(id).fo_zuordnung
        sighting = TblFundorte.query.get(fo_id)
    if sighting:
        # Update sighting with data from request
        # This will depend on how you implement
        # the saveChanges function in JavaScript
        # sighting.field = request.form['field']
        sighting.bearb_id = session["user_id"]
        if fieldname == "fo_quelle":
            sighting.fo_quelle = new_data
        elif fieldname == "anm_bearbeiter":
            sighting.anm_bearbeiter = new_data
        elif fieldname == "amt":
            sighting.amt = new_data
        elif fieldname == "mtb":
            sighting.mtb = new_data
        elif fieldname == "latitude":
            sighting.latitude = new_data
        elif fieldname == "longitude":
            sighting.longitude = new_data
        db.session.commit()
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Report not found"}), 404


@admin.route("/<path:filename>")
def report_Img(filename):
    "This function is used to serve the image of the report"
    return send_from_directory("", filename, mimetype="image/webp", as_attachment=False)


@admin.route("/toggle_approve_sighting/<id>", methods=["POST"])
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
        sighting.bearb_id = session["user_id"]
        db.session.commit()
        current_app.logger.debug(
            f"Sighting {id} approval toggled. dat_bear set to {sighting.dat_bear}"
        )
    else:
        current_app.logger.error(f"Sighting {id} not found for approval toggle.")
        return jsonify({"error": "Report not found"}), 404

    if Config.send_emails:
        # get data for E-Mail if send_email is True
        sighting = (
            db.session.query(
                TblMeldungen,
                TblFundorte,
                TblFundortBeschreibung,
                TblMeldungUser,
                TblUsers,
            )
            .join(TblFundorte, TblMeldungen.fo_zuordnung == TblFundorte.id)
            .join(
                TblFundortBeschreibung,
                TblFundorte.beschreibung == TblFundortBeschreibung.id,
            )
            .join(TblMeldungUser, TblMeldungen.id == TblMeldungUser.id_meldung)
            .join(TblUsers, TblMeldungUser.id_user == TblUsers.id)
            .filter(TblMeldungen.id == id)
            .first()
        )

        if sighting:
            dbdata = {}
            for part in sighting:
                part_dict = {
                    c.name: getattr(part, c.name) for c in part.__table__.columns
                }
                dbdata.update(part_dict)

            if dbdata["user_kontakt"]:
                try:
                    send_email(dbdata)
                except Exception as e:
                    current_app.logger.error(
                        f"Email not sent for sighting {id}. Error: {e}"
                    )
            else:
                current_app.logger.error(
                    f"Email not sent for sighting {id}. No email address found."
                )
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Sighting not found for email sending."}), 404
    else:
        return jsonify({"success": True})


@admin.route("/get_sighting/<id>", methods=["GET", "POST"])
@login_required
def get_sighting(id):
    "Find the sighting by id and return it as a JSON object"
    # Find the report by id
    sighting = (
        db.session.query(
            TblMeldungen, TblFundorte, TblFundortBeschreibung, TblMeldungUser, TblUsers
        )
        .join(TblFundorte, TblMeldungen.fo_zuordnung == TblFundorte.id)
        .join(
            TblFundortBeschreibung,
            TblFundorte.beschreibung == TblFundortBeschreibung.id,
        )
        .join(TblMeldungUser, TblMeldungen.id == TblMeldungUser.id_meldung)
        .join(TblUsers, TblMeldungUser.id_user == TblUsers.id)
        .filter(TblMeldungen.id == id)
        .first()
    )

    if sighting:
        # Convert sighting to a dictionary and return it
        sighting_dict = {}
        for part in sighting:
            part_dict = {c.name: getattr(part, c.name) for c in part.__table__.columns}
            sighting_dict.update(part_dict)
        return jsonify(sighting_dict)
    else:
        return jsonify({"error": "Report not found"}), 404


@admin.route("/delete_sighting/<id>", methods=["POST"])
@login_required
def delete_sighting(id):
    "Delete sighting based on id"
    # Find the report by id
    sighting = TblMeldungen.query.get(id)
    if sighting:
        # Set the deleted value to True
        sighting.deleted = True
        sighting.bearb_id = session["user_id"]
        db.session.commit()
        return jsonify({"message": "Report successfully deleted"}), 200
    else:
        return jsonify({"error": "Report not found"}), 404


@admin.route("/undelete_sighting/<id>", methods=["POST"])
@login_required
def undelete_sighting(id):
    "Undelete sighting based on id"
    # Find the report by id
    sighting = TblMeldungen.query.get(id)
    if sighting:
        # Set the deleted value to False
        sighting.deleted = False
        sighting.bearb_id = session["user_id"]
        db.session.commit()
        return jsonify({"message": "Report successfully undeleted"}), 200
    else:
        return jsonify({"error": "Report not found"}), 404


@admin.route("/change_mantis_gender/<int:id>", methods=["POST"])
@login_required
def change_gender(id):
    "Change mantis gender or type"
    new_gender = request.form.get("new_gender")

    sighting = TblMeldungen.query.get(id)

    # Reset all gender columns to 0
    sighting.art_m = 0
    sighting.art_w = 0
    sighting.art_n = 0
    sighting.art_o = 0
    sighting.art_f = 0

    # Update the specified gender to 1
    if new_gender == "M":
        sighting.art_m = 1
    elif new_gender == "W":
        sighting.art_w = 1
    elif new_gender == "N":
        sighting.art_n = 1
    elif new_gender == "O":
        sighting.art_o = 1
    elif new_gender == "F":
        sighting.art_f = 1

    sighting.bearb_id = session["user_id"]
    db.session.commit()

    return jsonify(success=True)


@admin.route("/change_mantis_count/<int:id>", methods=["POST"])
@login_required
def change_mantis_count(id):
    "Change mantis count for a specific type"
    new_count = request.form.get("new_count")
    mantis_type = request.form.get("type")
    sighting = TblMeldungen.query.get(id)

    # Update the count for the specified mantis type
    if mantis_type == "Männchen":
        sighting.art_m = new_count
    elif mantis_type == "Weibchen":
        sighting.art_w = new_count
    elif mantis_type == "Nymphe":
        sighting.art_n = new_count
    elif mantis_type == "Oothek":
        sighting.art_o = new_count
    elif mantis_type == "Andere":
        sighting.art_f = new_count
    elif mantis_type == "Anzahl":
        sighting.tiere = new_count

    sighting.bearb_id = session["user_id"]
    db.session.commit()

    return jsonify(success=True)


@admin.route("/admin/export/xlsx/<string:value>")
@login_required
def export_data(value):
    "Export the data from the database as an Excel file"
    try:
        current_time = datetime.now().strftime("%d.%m.%Y_%H%M")

        if value == "all":
            data = perform_query()
            filename = f"Alle_Meldungen_{current_time}.xlsx"
        elif value == "accepted":
            data = perform_query(filter_value=True)
            filename = f"Akzeptierte_Meldungen_{current_time}.xlsx"
        elif value == "non_accepted":
            data = perform_query(filter_value=False)
            filename = f"Nicht_akzeptierte_Meldungen_{current_time}.xlsx"
        else:
            abort(404, description="Resource not found")

        data_dicts = [row2dict(row) for row in data]
        df = pd.DataFrame(data_dicts)

        # Write the DataFrame to an Excel file
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Daten", index=False)
            
            # Get the xlsxwriter workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets["Daten"]
            
            # Add a table to the worksheet
            (max_row, max_col) = df.shape
            column_settings = [{'header': column} for column in df.columns]
            worksheet.add_table(0, 0, max_row, max_col - 1, {
                'columns': column_settings,
                'style': 'Table Style Medium 9'
            })
            
            # Auto-adjust columns' width
            for i, col in enumerate(df.columns):
                column_len = max(df[col].astype(str).map(len).max(), len(col))
                worksheet.set_column(i, i, column_len + 2)

        # Reset the file pointer to the beginning
        output.seek(0)

        # Send the file
        mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return send_file(output, mimetype=mime, as_attachment=True, download_name=filename)
    except Exception as e:
        current_app.logger.exception("Error in export_data")
        return jsonify({"error": "An error occurred during export"}), 500


def update_report_image_date(report_id, new_date):
    "Update the date in the image filename and the database"
    new_date_obj = datetime.strptime(new_date, "%Y-%m-%d")

    # Fetch the report
    report = db.session.query(TblMeldungen).filter_by(id=report_id).first()
    if not report:
        return {"error": "Report not found"}, 404

    # Fetch the corresponding fundorte record
    fundorte_record = (
        db.session.query(TblFundorte).filter_by(id=report.fo_zuordnung).first()
    )
    if not fundorte_record:
        return {"error": "Fundorte record not found"}, 404

    base_dir = Path(current_app.config["UPLOAD_FOLDER"])
    old_image_path = base_dir / fundorte_record.ablage

    old_dir, old_filename = os.path.split(old_image_path)
    location, _, usrid = old_filename.rsplit("-", 2)

    old_dir, old_filename = os.path.split(old_image_path)
    location, _, usrid = old_filename.rsplit("-", 2)

    new_dir_path = _create_directory(new_date_obj)
    new_filename = _create_filename(location, usrid, new_date_obj)
    new_file_path = new_dir_path / (new_filename + ".webp")

    try:
        shutil.move(str(old_image_path), str(new_file_path))

        # Check if old directory is empty, if yes, delete it
        if not os.listdir(old_dir):
            os.rmdir(old_dir)

    except IOError as e:
        return {"error": f"Failed to move file: {e}"}, 500

    # Update the path in fundorte table
    fundorte_record.ablage = str(new_file_path.relative_to(base_dir))
    db.session.commit()

    return {"status": "success"}, 200


def _create_directory(new_date):
    "Create a directory for the new image if it doesn't exist yet"
    year = new_date.strftime("%Y")
    base_dir = Path(current_app.config["UPLOAD_FOLDER"])
    dir_path = base_dir / year / new_date.strftime("%Y-%m-%d")
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def _create_filename(location, usrid, new_date):
    "Create a filename for the new image and location"
    new_timestamp = new_date.strftime("%Y%m%d%H%M%S")
    # Generate the filename without the .webp extension
    return "{}-{}-{}".format(
        secure_filename(location), new_timestamp, secure_filename(usrid)
    )


# Define a function to convert a row to a dictionary
def row2dict(row):
    "Convert a row to a dictionary"
    d = {}
    for item in row:
        for column in item.__table__.columns:
            d[column.name] = str(getattr(item, column.name))

    return d


def perform_query(filter_value=None):
    "Perform a query to get all data from the database"
    # Create a session
    Session = sessionmaker(bind=db.engine)
    session = Session()

    query = (
        session.query(
            TblMeldungen, TblFundorte, TblFundortBeschreibung, TblMeldungUser, TblUsers
        )
        .join(TblFundorte, TblMeldungen.fo_zuordnung == TblFundorte.id)
        .join(
            TblFundortBeschreibung,
            TblFundorte.beschreibung == TblFundortBeschreibung.id,
        )
        .join(TblMeldungUser, TblMeldungen.id == TblMeldungUser.id_meldung)
        .join(TblUsers, TblMeldungUser.id_user == TblUsers.id)
    )

    return query.all()


@admin.route("/alldata")
@login_required
def database_view():
    inspector = inspect(db.engine)
    tables = [table for table in inspector.get_table_names() if table not in ['aemter', 'alembic_version', 'melduser']]
    tables.append('all_data_view')  # Add the materialized view to the list of tables
    
    # Get user_id from session, default to None if not found
    user_id = session.get('user_id')
    
    return render_template("admin/database.html", tables=tables, user_id=user_id)

@admin.route("/admin/get_table_data/<table_name>")
@login_required
def get_table_data(table_name):
    if table_name in ['aemter', 'alembic_version']:
        return jsonify({"error": "Access to this table is not allowed"}), 403
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        search_type = request.args.get('search_type', 'full_text')  # Get search type
        sort_column = request.args.get('sort_column', 'id')
        sort_direction = request.args.get('sort_direction', 'asc')

        # Check if it's time to refresh the materialized view
        last_updated = session.get('last_updated_all_data_view')
        now = datetime.utcnow()
        if last_updated is None or (now - last_updated.replace(tzinfo=None) > timedelta(minutes=1)):
            TblAllData.refresh_materialized_view()
            session['last_updated_all_data_view'] = now

        # Get the table object
        if table_name == 'all_data_view':
            table = TblAllData.__table__
        else:
            table = db.metadata.tables.get(table_name)
        
        if table is None:
            return jsonify({"error": "Table not found"}), 404

        columns = [column.name for column in table.columns]

        # Validate sort_column to prevent SQL injection
        if sort_column not in columns:
            sort_column = 'id'

        # Create a select statement
        stmt = db.select(table)

        # Apply search filter if search term is provided
        if search:
            if search_type == 'id':
                try:
                    # Try to convert search term to integer for ID search
                    search_id = int(search)
                    stmt = stmt.where(table.c.id == search_id)
                except ValueError:
                    # If conversion fails, return no results
                    stmt = stmt.where(table.c.id == -1)  # This ensures no results
            else:  # full_text search
                search_filters = []
                for column in table.columns:
                    if isinstance(column.type, db.String):
                        search_filters.append(column.ilike(f'%{search}%'))
                    elif isinstance(column.type, (db.Integer, db.Float)):
                        search_filters.append(cast(column, String).ilike(f'%{search}%'))
                if search_filters:
                    stmt = stmt.where(or_(*search_filters))

        # Apply sorting
        if sort_direction == 'asc':
            stmt = stmt.order_by(table.c[sort_column].asc())
        else:
            stmt = stmt.order_by(table.c[sort_column].desc())

        # Get total count for pagination
        total_items_stmt = db.select(db.func.count()).select_from(table)
        if search:
            if search_type == 'id':
                try:
                    search_id = int(search)
                    total_items_stmt = total_items_stmt.where(table.c.id == search_id)
                except ValueError:
                    total_items_stmt = total_items_stmt.where(table.c.id == -1)
            else:
                if search_filters:
                    total_items_stmt = total_items_stmt.where(or_(*search_filters))
        total_items = db.session.execute(total_items_stmt).scalar()

        # Apply pagination
        stmt = stmt.offset((page - 1) * per_page).limit(per_page)

        # Execute query and get results
        results = db.session.execute(stmt).fetchall()

        def get_standard_type(column_type):
            if isinstance(column_type, db.Integer):
                return 'integer'
            elif isinstance(column_type, db.String):
                return 'string'
            elif isinstance(column_type, db.Boolean):
                return 'boolean'
            elif isinstance(column_type, db.Date):
                return 'date'
            elif isinstance(column_type, db.DateTime):
                return 'datetime'
            elif isinstance(column_type, db.Float):
                return 'float'
            else:
                return 'string'

        # Get column names and types
        column_types = {column.name: get_standard_type(column.type) for column in table.columns}

        # Exclude sensitive columns
        EXCLUDED_COLUMNS = ['report_user_db_id', 'fundorte_id', 'beschreibung_id', 'dat_fund_bis', 'fo_beleg', 'bearb_id', 'ablage']
        columns_with_excluded = columns.copy()
        columns = [col for col in columns if col not in EXCLUDED_COLUMNS]
        column_types = {col: column_types[col] for col in columns}

        # Convert results to list of lists
        data = [
            [getattr(row, col) for col in columns_with_excluded if col not in EXCLUDED_COLUMNS]
            for row in results
        ]

        return jsonify({
            "columns": columns,
            "data": data,
            "column_types": column_types,
            "non_editable_fields": NON_EDITABLE_FIELDS.get(table_name, []),
            "total_items": total_items
        })
    except Exception as e:
        current_app.logger.exception("Error in get_table_data")
        return jsonify({"error": "An error occurred while fetching table data"}), 500

@admin.route("/admin/update_cell", methods=["POST"])
@login_required
def update_cell():
    data = request.json
    table_name = data['table']
    column_name = data['column']
    id_value = data['id']
    new_value = data['value']

    if table_name in NON_EDITABLE_FIELDS and column_name in NON_EDITABLE_FIELDS[table_name]:
        return jsonify({"error": "This field is not editable"}), 403

    try:
        if table_name == 'all_data_view':
            # Find the original table and column
            original_table, original_column = find_original_table_and_column(column_name)
            if not original_table or not original_column:
                return jsonify({"error": "Unable to find original table and column"}), 400

            # Fetch the corresponding row from all_data_view
            all_data_row = db.session.query(TblAllData).filter(TblAllData.id == id_value).first()
            if not all_data_row:
                return jsonify({"error": "Record not found"}), 404

            if original_table == TblUsers:
                user_db_id = all_data_row.report_user_db_id
                if not user_db_id:
                    return jsonify({"error": "User ID not found in the record"}), 400
                stmt = (
                    update(original_table)
                    .where(original_table.id == user_db_id)
                    .values(**{original_column: new_value})
                )
            elif original_table == TblFundorte:
                fundorte_id = all_data_row.fundorte_id
                if not fundorte_id:
                    return jsonify({"error": "Fundorte ID not found in the record"}), 400
                stmt = (
                    update(original_table)
                    .where(original_table.id == fundorte_id)
                    .values(**{original_column: new_value})
                )
            elif original_table == TblFundortBeschreibung:
                beschreibung_id = all_data_row.beschreibung_id
                if not beschreibung_id:
                    return jsonify({"error": "Beschreibung ID not found in the record"}), 400
                stmt = (
                    update(original_table)
                    .where(original_table.id == beschreibung_id)
                    .values(**{original_column: new_value})
                )
            else:
                # Update other tables using id_value (from meldungen)
                stmt = (
                    update(original_table)
                    .where(original_table.id == id_value)
                    .values(**{column_name: new_value})
                )
        else:
            # Get the table object
            table = db.metadata.tables.get(table_name)
            if table is None:
                return jsonify({"error": "Table not found"}), 404

            # Create the update statement
            stmt = (
                db.update(table)
                .where(table.c.id == id_value)
                .values(**{column_name: new_value})
            )

        # Execute the update
        result = db.session.execute(stmt)
        db.session.commit()

        if result.rowcount == 0:
            return jsonify({"error": "Record not found"}), 404

        # Refresh the materialized view after update
        TblAllData.refresh_materialized_view()

        return jsonify({"success": True})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "An error occurred while updating the cell"}), 500

def find_original_table_and_column(column_name):
    table_column_mapping = {
        'id': (TblMeldungen, 'id'),
        'deleted': (TblMeldungen, 'deleted'),
        'dat_fund_von': (TblMeldungen, 'dat_fund_von'),
        'dat_fund_bis': (TblMeldungen, 'dat_fund_bis'),
        'dat_meld': (TblMeldungen, 'dat_meld'),
        'dat_bear': (TblMeldungen, 'dat_bear'),
        'bearb_id': (TblMeldungen, 'bearb_id'),
        'tiere': (TblMeldungen, 'tiere'),
        'art_m': (TblMeldungen, 'art_m'),
        'art_w': (TblMeldungen, 'art_w'),
        'art_n': (TblMeldungen, 'art_n'),
        'art_o': (TblMeldungen, 'art_o'),
        'art_f': (TblMeldungen, 'art_f'),
        'fo_quelle': (TblMeldungen, 'fo_quelle'),
        'fo_beleg': (TblMeldungen, 'fo_beleg'),
        'anm_melder': (TblMeldungen, 'anm_melder'),
        'anm_bearbeiter': (TblMeldungen, 'anm_bearbeiter'),
        'plz': (TblFundorte, 'plz'),
        'ort': (TblFundorte, 'ort'),
        'strasse': (TblFundorte, 'strasse'),
        'kreis': (TblFundorte, 'kreis'),
        'land': (TblFundorte, 'land'),
        'amt': (TblFundorte, 'amt'),
        'mtb': (TblFundorte, 'mtb'),
        'longitude': (TblFundorte, 'longitude'),
        'latitude': (TblFundorte, 'latitude'),
        'ablage': (TblFundorte, 'ablage'),
        'beschreibung': (TblFundortBeschreibung, 'beschreibung'),
        'report_user_id': (TblUsers, 'user_id'),
        'report_user_name': (TblUsers, 'user_name'),
        'report_user_kontakt': (TblUsers, 'user_kontakt')
    }
    return table_column_mapping.get(column_name, (None, None))
