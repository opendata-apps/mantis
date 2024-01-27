import os
from dotenv import load_dotenv
from datetime import timedelta

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
    esri = os.environ.get('ESRI_MAP_KEY') or 'no-key-found'
    UPLOAD_FOLDER = 'app/datastore'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    CHECKLIST = {}
    PREFERRED_URL_SCHEME = 'https'
    INITIAL_DATA = [
        (1, 'Im Haus'),
        (2, 'Im Garten'),
        (3, 'Auf dem Balkon/auf der Terrasse'),
        (4, 'Am Fenster/an der Hauswand'),
        (5, 'Industriebrache'),
        (6, 'Im Wald'),
        (7, 'Wiese/Weide'),
        (8, 'Heidelandschaft'),
        (9, 'Straßengraben/Wegesrand/Ruderalflur'),
        (10, 'Gewerbegebiet'),
        (11, 'Im oder am Auto'),
        (99, 'Anderer Fundort')
    ]
