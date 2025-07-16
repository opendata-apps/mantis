import os
from dotenv import load_dotenv
from datetime import timedelta
from datetime import datetime

load_dotenv(dotenv_path="app/.env")

class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://mantis_user:mantis@localhost/mantis_tracker'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAP_CENTER_LONGITUDE = -122.4194
    MAP_CENTER_LATITUDE = 37.7749
    MAP_ZOOM = 1
    SECRET_KEY = os.environ.get(
        'SECRET_KEY') or 'do-not-get-tired-youll-never-find'
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
    STATIC_FOLDER = 'app/static'
    CURRENT_YEAR = datetime.now().year
    MIN_MAP_YEAR = 2023
    CELEBRATION_THRESHOLD = 10000
    TESTING = False
 
