import os
from dotenv import load_dotenv
from datetime import timedelta
from datetime import datetime

load_dotenv(dotenv_path="app/.env")

class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://mantis_user:mantis@localhost/mantis_tracker'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Connection Pooling Configuration
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,           # Core pool size (persistent connections)
        'max_overflow': 20,        # Additional connections during peak load
        'pool_recycle': 3600,      # Recycle connections after 1 hour (prevents stale connections)
        'pool_pre_ping': True,     # Test connections before use (prevents "server has gone away" errors)
    }
    MAP_CENTER_LONGITUDE = -122.4194
    MAP_CENTER_LATITUDE = 37.7749
    MAP_ZOOM = 1
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        # Generate a secure secret key in development
        import secrets
        SECRET_KEY = secrets.token_hex(32)
        # Warn in development that secret key is not set
        import warnings
        warnings.warn(
            "SECRET_KEY not set in environment variables. "
            "Using generated key. Set SECRET_KEY for production!",
            UserWarning
        )
    WTF_CSRF_ENABLED = True
    host = ""
    port = 25
    tls = True
    sender_email = ""
    sender_pass = ""
    send_emails = False
    UPLOAD_FOLDER = 'app/datastore'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    CHECKLIST = {}
    PREFERRED_URL_SCHEME = 'https'
    
    # Session Security Settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # DoS Prevention
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    MAX_FORM_MEMORY_SIZE = 500 * 1024  # 500KB max form data
    MAX_FORM_PARTS = 1000  # max 1000 form fields
    STATIC_FOLDER = 'app/static'
    CURRENT_YEAR = datetime.now().year
    MIN_MAP_YEAR = 2023
    CELEBRATION_THRESHOLD = 10000
    TESTING = False
 
