import os
from dotenv import load_dotenv
from datetime import timedelta

# Load .env file from project root
load_dotenv()

# Compute absolute paths based on project structure (Flask best practice)
# This ensures paths work regardless of current working directory
_config_dir = os.path.dirname(os.path.abspath(__file__))  # app/
_project_root = os.path.dirname(_config_dir)  # project root


def _resolve_upload_folder():
    """Resolve UPLOAD_FOLDER to an absolute path (Flask best practice).

    Priority:
    1. UPLOAD_FOLDER env var (must be absolute path)
    2. Default: app/datastore (for local development)

    Container: UPLOAD_FOLDER=/mantis/app/datastore (mirrors host structure)

    Raises ValueError if env var contains a relative path.
    """
    env_path = os.getenv("UPLOAD_FOLDER")
    if env_path:
        if not os.path.isabs(env_path):
            raise ValueError(
                f"UPLOAD_FOLDER must be an absolute path, got: '{env_path}'. "
                f"For containers, use UPLOAD_FOLDER=/data (the mount point)."
            )
        return env_path
    return os.path.join(_config_dir, "datastore")


def _resolve_backup_dir():
    """Resolve BACKUP_DIR to an absolute path."""
    env_path = os.getenv("BACKUP_DIR")
    if env_path:
        if not os.path.isabs(env_path):
            raise ValueError(f"BACKUP_DIR must be an absolute path, got: '{env_path}'.")
        return env_path
    return os.path.join(_project_root, "backups")


def _env_or_default(name: str, default: str) -> str:
    value = os.getenv(name)
    return default if value is None or value == "" else value


class Config:
    # Database Configuration (constructed from components, like Superset/Paperless-ngx)
    # Container deployments override DATABASE_HOST=db via docker-compose environment.
    DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
    DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
    DATABASE_USER = os.getenv("POSTGRES_USER", "mantis_user")
    DATABASE_PASSWORD = os.getenv("POSTGRES_PASSWORD", "mantis")
    DATABASE_DB = os.getenv("POSTGRES_DB", "mantis_tracker")

    SQLALCHEMY_DATABASE_URI = (
        f"postgresql+psycopg://{DATABASE_USER}:{DATABASE_PASSWORD}"
        f"@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_DB}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Connection Pooling Configuration
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": int(os.getenv("DB_POOL_SIZE", 10)),
        "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", 20)),
        "pool_recycle": int(os.getenv("DB_POOL_RECYCLE", 3600)),
        "pool_pre_ping": True,
    }

    # Map Configuration
    MIN_MAP_YEAR = 2023

    # Security Configuration
    # FLASK_ENV was removed in Flask 3.0 — use FLASK_DEBUG as the dev indicator.
    # When DEBUG is not explicitly enabled, SECRET_KEY is mandatory.
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        if os.getenv("FLASK_DEBUG", "0") not in ("1", "true", "True"):
            raise ValueError(
                "SECRET_KEY must be set when FLASK_DEBUG is not enabled. "
                'Generate one with: python -c "import secrets; print(secrets.token_hex(32))"'
            )
        import secrets

        SECRET_KEY = secrets.token_hex(32)
    WTF_CSRF_ENABLED = True

    # Email Configuration
    MAIL_SERVER = _env_or_default("MAIL_SERVER", "mail.mantis-projekt.de")
    MAIL_PORT = int(_env_or_default("MAIL_PORT", "25"))
    MAIL_USE_TLS = _env_or_default("MAIL_USE_TLS", "True").lower() in (
        "true",
        "1",
        "yes",
    )
    MAIL_USE_SSL = _env_or_default("MAIL_USE_SSL", "False").lower() in (
        "true",
        "1",
        "yes",
    )
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = (
        _env_or_default("MAIL_DEFAULT_SENDER_NAME", "Mantis-Projekt"),
        _env_or_default("MAIL_DEFAULT_SENDER", "mantis@projekt.de"),
    )
    REVIEWERMAIL = os.getenv("REVIEWERMAIL", "False").lower() in ("true", "1", "yes")
    BACKUPMAIL = os.getenv("BACKUPMAIL", "").strip()
    BACKUP_DOWNLOAD_MAX_AGE_SECONDS = int(
        os.getenv("BACKUP_DOWNLOAD_MAX_AGE_SECONDS", str(7 * 24 * 60 * 60))
    )

    # Upload Configuration - always absolute path (Flask best practice)
    UPLOAD_FOLDER = _resolve_upload_folder()
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "heic", "heif"}
    BACKUP_DIR = _resolve_backup_dir()

    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    PREFERRED_URL_SCHEME = os.getenv("PREFERRED_URL_SCHEME", "https")
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "True").lower() in (
        "true",
        "1",
        "yes",
    )
    SESSION_COOKIE_HTTPONLY = True  # Always True for security
    SESSION_COOKIE_SAMESITE = "Lax"  # Always Lax for CSRF protection

    # DoS Prevention (Static Security Settings)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    MAX_FORM_MEMORY_SIZE = 500 * 1024  # 500KB max form data
    MAX_FORM_PARTS = 1000  # max 1000 form fields

    # Application Settings
    STATIC_FOLDER = os.path.join(_config_dir, "static")
    FAVICON_BUILD_DIR = os.path.join(_config_dir, "static", "favicon")
    CELEBRATION_THRESHOLD = int(os.getenv("CELEBRATION_THRESHOLD", "10000"))
