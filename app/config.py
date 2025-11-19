import os
from dotenv import load_dotenv
from datetime import timedelta
from datetime import datetime

# Load .env file from project root
load_dotenv()

class Config:
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'SQLALCHEMY_DATABASE_URI',
        'postgresql://mantis_user:mantis@localhost/mantis_tracker'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Connection Pooling Configuration
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.getenv('DB_POOL_SIZE', 10)),
        'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', 20)),
        'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', 3600)),
        'pool_pre_ping': True,
    }

    # Map Configuration (Static - Brandenburg, Germany)
    MAP_CENTER_LONGITUDE = 13.0
    MAP_CENTER_LATITUDE = 52.4
    MAP_ZOOM = 8
    MIN_MAP_YEAR = 2023

    # Security Configuration
    SECRET_KEY = os.getenv('SECRET_KEY')
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

    # Email Configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'mail.mantis-projekt.de')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 25))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'False').lower() in ('true', '1', 'yes')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = (
        os.getenv('MAIL_DEFAULT_SENDER_NAME', 'Mantis-Projekt'),
        os.getenv('MAIL_DEFAULT_SENDER', 'mantis@projekt.de')
    )
    REVIEWERMAIL = os.getenv('REVIEWERMAIL', 'False').lower() in ('true', '1', 'yes')

    # Upload Configuration
    UPLOAD_FOLDER = 'app/datastore'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    PREFERRED_URL_SCHEME = os.getenv('PREFERRED_URL_SCHEME', 'https')
    SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'True').lower() in ('true', '1', 'yes')
    SESSION_COOKIE_HTTPONLY = True  # Always True for security
    SESSION_COOKIE_SAMESITE = 'Lax'  # Always Lax for CSRF protection

    # DoS Prevention (Static Security Settings)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    MAX_FORM_MEMORY_SIZE = 500 * 1024  # 500KB max form data
    MAX_FORM_PARTS = 1000  # max 1000 form fields

    # Application Settings
    STATIC_FOLDER = 'app/static'
    CURRENT_YEAR = datetime.now().year
    CELEBRATION_THRESHOLD = int(os.getenv('CELEBRATION_THRESHOLD', '10000'))
    TESTING = os.getenv('TESTING', 'False').lower() in ('true', '1', 'yes')
    CHECKLIST = {}
 
