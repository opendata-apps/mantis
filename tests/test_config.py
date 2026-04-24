import os

from app.database.populate import INITIAL_BESCHREIBUNG_DATA

# Compute absolute paths based on project structure (Flask best practice)
_config_dir = os.path.dirname(os.path.abspath(__file__))  # app/
_project_root = os.path.dirname(_config_dir)  # project root


class Config:
    TESTING = True
    URI = "postgresql+psycopg://mantis_user:mantis@localhost/mantis_tester"
    SQLALCHEMY_DATABASE_URI = URI
    DATABASE_HOST = "localhost"
    DATABASE_PORT = "5432"
    DATABASE_USER = "mantis_user"
    DATABASE_PASSWORD = "mantis"
    DATABASE_DB = "mantis_tester"
    INITIAL_DATA = INITIAL_BESCHREIBUNG_DATA

    MIN_MAP_YEAR = 2025
    CELEBRATION_THRESHOLD = 10000
    SECRET_KEY = os.environ.get("SECRET_KEY") or "do-not-get-tired-youll-never-find"
    BACKUPMAIL = "backup@example.com"
    BACKUP_DOWNLOAD_MAX_AGE_SECONDS = 604800

    # Upload Configuration - always absolute path (Flask best practice)
    UPLOAD_FOLDER = os.path.join(_project_root, "datastore")
    BACKUP_DIR = os.path.join(_project_root, "backups")

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing
    RATELIMIT_ENABLED = False  # Disable rate limiting for testing
