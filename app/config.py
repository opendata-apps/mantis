import os
from datetime import timedelta
from email.utils import parseaddr

from dotenv import load_dotenv
from sqlalchemy import URL

# Load .env file from project root
load_dotenv()

# Compute absolute paths based on project structure (Flask best practice)
# This ensures paths work regardless of current working directory
_config_dir = os.path.dirname(os.path.abspath(__file__))  # app/
_project_root = os.path.dirname(_config_dir)  # project root


def _resolve_upload_folder():
    """UPLOAD_FOLDER from the environment, else app/datastore; must be absolute."""
    env_path = os.getenv("UPLOAD_FOLDER")
    if env_path:
        if not os.path.isabs(env_path):
            raise ValueError(
                f"UPLOAD_FOLDER must be an absolute path, got: '{env_path}'."
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


def _env_int(name: str, default: int) -> int:
    """Read a whole-number setting, treating an empty value as unset.

    os.getenv's default only applies when the key is absent. A key left blank in
    .env reaches int() as "", which raises at import time.
    """
    value = _env_or_default(name, str(default))
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"{name} must be a whole number, got: '{value}'.") from None


def _resolve_mail_sender(name: str, address: str) -> tuple[str, str]:
    """Resolve the From address, rejecting anything smtplib cannot parse.

    An unparseable address does not raise anywhere in Flask-Mail: the From
    header degrades to a bare display name and smtplib falls back to the null
    sender `MAIL FROM:<>`, so every mail leaves as an unattributable bounce and
    is filtered by the recipient. Failing at startup is the only loud moment.
    """
    parsed = parseaddr(address)[1]
    if "@" not in parsed:
        raise ValueError(
            f"MAIL_DEFAULT_SENDER must be a plain email address, got: '{address}'. "
            f"Use MAIL_DEFAULT_SENDER=post@example.com and set the display name "
            f"in MAIL_DEFAULT_SENDER_NAME."
        )
    return (name, parsed)


class Config:
    # Database Configuration (constructed from components, like Superset/Paperless-ngx)
    # Container deployments override DATABASE_HOST=db via docker-compose environment.
    DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
    # Stays a string: _run_pg_dump passes it straight into a command list.
    DATABASE_PORT = _env_or_default("DATABASE_PORT", "5432")
    DATABASE_USER = os.getenv("POSTGRES_USER", "mantis_user")
    DATABASE_PASSWORD = os.getenv("POSTGRES_PASSWORD", "mantis")
    DATABASE_DB = os.getenv("POSTGRES_DB", "mantis_tracker")

    # URL.create escapes the credentials; interpolating them into a string
    # misparses a password containing @ / : # or %. Rendered back to a string
    # because alembic's set_main_option and sqlalchemy_utils both want one —
    # with hide_password=False, since str(URL) would emit "***".
    SQLALCHEMY_DATABASE_URI = URL.create(
        "postgresql+psycopg",
        username=DATABASE_USER,
        password=DATABASE_PASSWORD,
        host=DATABASE_HOST,
        port=int(DATABASE_PORT),
        database=DATABASE_DB,
    ).render_as_string(hide_password=False)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SQLAlchemy's defaults. Each gunicorn worker has its own pool, so keep
    # (pool_size + max_overflow) × workers under Postgres' max_connections, or a
    # leak locks out psql and the backup too.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": _env_int("DB_POOL_SIZE", 5),
        "max_overflow": _env_int("DB_MAX_OVERFLOW", 10),
        "pool_recycle": _env_int("DB_POOL_RECYCLE", 3600),
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
    # Valid for the session (an idle hour, see the factory), not an hour from
    # issue: filling in a report can take longer.
    WTF_CSRF_TIME_LIMIT = None

    # Email Configuration
    MAIL_SERVER = _env_or_default("MAIL_SERVER", "mail.mantis-projekt.de")
    MAIL_PORT = _env_int("MAIL_PORT", 25)
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
    MAIL_DEFAULT_SENDER = _resolve_mail_sender(
        _env_or_default("MAIL_DEFAULT_SENDER_NAME", "Mantis-Projekt"),
        _env_or_default("MAIL_DEFAULT_SENDER", "mantis@projekt.de"),
    )
    REVIEWERMAIL = os.getenv("REVIEWERMAIL", "False").lower() in ("true", "1", "yes")
    BACKUPMAIL = os.getenv("BACKUPMAIL", "").strip()

    # Public support intake for photos the browser cannot upload. GitLab creates
    # confidential tickets; knowing this address does not grant access to them.
    PHOTO_SUPPORT_EMAIL = os.getenv(
        "PHOTO_SUPPORT_EMAIL",
        "contact-project+opendata-apps-mantis-41791538-issue-@incoming.gitlab.com",
    )
    # Two, not one: most reporters retry once on their own (67 logged failures
    # across 39 distinct files), so the first failure is not yet a dead end.
    PHOTO_ESCALATE_AFTER = _env_int("PHOTO_ESCALATE_AFTER", 2)

    # Upload Configuration - always absolute path (Flask best practice)
    UPLOAD_FOLDER = _resolve_upload_folder()
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

    # Reporters only — see app.auth.log_in.
    REMEMBER_COOKIE_NAME = "mantis_reporter"
    # Copies the value, not a link — a subclass overriding SESSION_COOKIE_SECURE
    # alone leaves this one as it was. Override both (tests/test_config.py does).
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    REMEMBER_COOKIE_SAMESITE = "Lax"

    # DoS Prevention (Static Security Settings)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    MAX_FORM_MEMORY_SIZE = 500 * 1024  # 500KB max form data
    MAX_FORM_PARTS = 1000  # max 1000 form fields

    # Application Settings
    FAVICON_BUILD_DIR = os.path.join(_config_dir, "static", "favicon")
    CELEBRATION_THRESHOLD = _env_int("CELEBRATION_THRESHOLD", 10000)
