"""Unbound extension instances, bound by ``init_app`` in the factory.

Imports nothing from ``app``, so a module the factory imports can read these
without hitting a half-initialised package.
https://flask.palletsprojects.com/en/stable/extensiondev/
"""

import os

from flask_favicon import FlaskFavicon
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()
db = SQLAlchemy()
migrate = Migrate()
# Counters live in each worker's memory, so with the 4 gunicorn workers every
# limit is effectively 4x and resets on deploy. Accepted: there is no shared
# store to point at. Passing memory:// explicitly keeps flask-limiter from
# warning about it on every start.
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
    strategy="fixed-window",
    default_limits=["200 per day", "100 per hour"],
    headers_enabled=True,
)
mail = Mail()
flask_favicon = FlaskFavicon()
# Leave session_protection at "basic": "strong" drops the session when the
# client address changes, logging reporters out mid-form on mobile/wifi switch.
login_manager = LoginManager()
