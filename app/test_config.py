import os
from datetime import datetime

class Config:
    TESTING = True
    URI = 'postgresql://mantis_user:mantis@localhost/mantis_tester'
    SQLALCHEMY_DATABASE_URI = URI
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

    CURRENT_YEAR = datetime.now().year
    MIN_MAP_YEAR = 2025
    CELEBRATION_THRESHOLD = 10000
    SECRET_KEY = os.environ.get(
        'SECRET_KEY') or 'do-not-get-tired-youll-never-find'
    UPLOAD_FOLDER = 'app/datastore'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing
    RATELIMIT_ENABLED = False  # Disable rate limiting for testing
