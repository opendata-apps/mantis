"""Production defaults with test database, HTTP-client and mail settings.

The test_config fixture supplies temporary filesystem paths per test.
"""

from app.config import Config as AppConfig
from app.database.populate import INITIAL_BESCHREIBUNG_DATA


class Config(AppConfig):
    # MAIL_SUPPRESS_SEND defaults to this, so the inherited MAIL_* cannot send.
    TESTING = True

    # --- Own database, never the developer's ---
    DATABASE_DB = "mantis_tester"
    URI = "postgresql+psycopg://mantis_user:mantis@localhost/mantis_tester"
    SQLALCHEMY_DATABASE_URI = URI
    INITIAL_DATA = INITIAL_BESCHREIBUNG_DATA

    # --- Pinned: env-dependent, must not vary by machine ---
    # Not inherited from AppConfig, which never declares it: app.config.py's
    # load_dotenv() puts the developer's FLASK_DEBUG into os.environ, and Flask
    # reads it in Flask.__init__ before from_object() runs. Unpinned, a .env with
    # FLASK_DEBUG=1 skips ProxyFix and the logging setup in the factory, so the
    # suite would cover different code than production runs.
    DEBUG = False
    SECRET_KEY = "do-not-get-tired-youll-never-find"
    REVIEWERMAIL = False  # gates the determination-mail branch in admin/reviewer.py
    MIN_MAP_YEAR = 2025

    # The test client speaks http. Both needed — see app/config.py.
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False

    # --- Neutralised: must never reach a real inbox or tracker ---
    BACKUPMAIL = "backup@example.com"
    PHOTO_SUPPORT_EMAIL = "photo-errors@example.com"

    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
