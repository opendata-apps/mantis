"""Passwordless auth: an unguessable URL is the credential.

`/sichtungen/<usrid>` and `/reviewer/<usrid>` grant whoever holds them
(https://www.w3.org/TR/capability-urls/). `TblUsers.get_id` returns that same
token, so the cookies expose nothing the URL does not.
"""

from functools import wraps

from flask import abort, session
from flask_login import current_user, login_required, login_user
from sqlalchemy import select

from app.database.models import TblUsers, UserRole
from app.extensions import db, login_manager


# Registered at import time; the route blueprints are what pull this module in.
@login_manager.user_loader
def load_user(user_id):
    return db.session.scalar(select(TblUsers).where(TblUsers.user_id == user_id))


@login_manager.unauthorized_handler
def unauthorized():
    # Drop the unresolvable id, or it gets looked up again on every request.
    session.pop("_user_id", None)
    # No login form exists, and reviewer endpoints must not leak auth state.
    abort(403)


def log_in(user):
    """Log a user in. Reporters are remembered; without that a repeat
    submission mints a second identity and splits their history."""
    login_user(user, remember=user.user_rolle == UserRole.REPORTER)


def reviewer_required(f):
    """Require a valid reviewer session with role '9'."""

    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.user_rolle != UserRole.REVIEWER:
            abort(403)
        return f(*args, **kwargs)

    return decorated_function
