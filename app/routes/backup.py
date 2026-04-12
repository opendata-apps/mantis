import subprocess
import os
import tempfile
import zipfile
import os
from dotenv import load_dotenv
from datetime import timedelta

from flask import (
    Blueprint,
    abort,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_file,
    send_from_directory,
    url_for,
    current_app,
    session,
    send_file
)

from app.database.models import (
    TblFundortBeschreibung,
    TblFundorte,
    TblMeldungen,
    TblMeldungUser,
    TblUsers,
    TblAllData,
    ReportStatus,
)
from app import db
from sqlalchemy import update, select, func
from datetime import datetime
from datetime import date
from app.tools.send_backup_email import send_backup_email

# Load .env file from project root
load_dotenv()

# DB-Zugangsdaten
DB_HOST = os.getenv("DATABASE_HOST", "localhost")
DB_NAME =  os.getenv("POSTGRES_DB", "mantis_tracker")
DB_USER = os.getenv("POSTGRES_USER", "mantis_user")
DB_PORT = os.getenv("DATABASE_PORT", "5432")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "mantis")
BACKUP_DIR = "/tmp"

# Blueprints
backup = Blueprint("backup", __name__)

# Pfad für temporäre Dateien (anpassen, falls erforderlich)
TMP_DIR = tempfile.mkdtemp()
BACKUP_DIR = "/tmp"

#@backup.route('/getlistofyears', methods=['GET'])
#def _get_list_of_years():
    
    

@backup.route('/export/<year>', methods=['GET'])
def trigger_dump(year: int):                                                          
    """Save images for given year as zip

    - create list of filenames
    - pg_dump
    - merge all files 
    - generate email for download
    
    """

    backup_file = f"/tmp/dump_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.sql"
    date_from = request.args.get("dateFrom", f"{year}-01-01")
    date_to = request.args.get("dateTo", f"{year}-12-31")
    
    try:
        # pg_dump als subprocess ausführen
        subprocess.run(
            [
                "pg_dump", "-U", DB_USER, "-h", DB_HOST, "-p", DB_PORT, DB_NAME
            ],
            env={**os.environ, "PGPASSWORD": DB_PASSWORD},  # Passwort über Umgebungsvariable
            stdout=open(backup_file, "w"),
            check=True
        )
        # Liste für den Bildexport generieren                                             
        stmt = (
            select(
                TblFundorte.ablage.label("ablage")
            )
            .join(TblMeldungen)
            .where(
                TblMeldungen.dat_meld >= date.fromisoformat(date_from),
                TblMeldungen.dat_meld <= date.fromisoformat(date_to),
            )
        )                                                                            
    
        result =  db.session.scalars(stmt)
        pfade = list(result)
        zip_name = f"/mantis/backup/backup_{year}.zip"
        # ZIP-Datei erstellen
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for datei in pfade:
                file_in_datastore = "/mantis/app/datastore/"+ datei
                if os.path.isfile(file_in_datastore):  # nur existierende Dateien
                     zipf.write(file_in_datastore, os.path.basename(file_in_datastore))
                else:
                    print(f"Warning: file not found -> {file_in_datastore}")
            zipf.write(backup_file, os.path.basename(backup_file))
         
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    data = {
        "user_kontakt": current_app.config.get("BACKUPMAIL", False),
        "backup": f"backup_{year}.zip",
        "sender": current_app.config.get("MAIL_DEFAULT_SENDER")
    }

    if data['user_kontakt']:
        try:
            send_backup_email(data)
        except Exception as e:
            current_app.logger.error(
                f"Email not sent for backup. Error: {e}"
            )
    return f"{year} gesichert"


@backup.route('/save/<backupfile>')
def download_file(backupfile=None):
    if backupfile:
        return send_file(
            f'/mantis/backup/{backupfile}',
            as_attachment=True
        )
        
if __name__ == '__main__':
   app.run(debug=True)
   
