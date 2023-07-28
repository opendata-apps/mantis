import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="app/.env")


class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost/mantis_tracker'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAP_CENTER_LONGITUDE = -122.4194
    MAP_CENTER_LATITUDE = 37.7749
    MAP_ZOOM = 1
    SECRET_KEY = os.environ.get(
        'SECRET_KEY') or 'do-not-get-tired-youll-never-find'
    WTF_CSRF_ENABLED = True
    UPLOAD_PATH = "datastore"
    host = ""
    port = 25
    tls = True
    sender_email = ""
    sender_pass = ""
    esri = os.environ.get('ESRI_MAP_KEY') or 'no-key-found'
