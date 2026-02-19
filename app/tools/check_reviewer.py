from functools import wraps
from flask import abort, g, session
from sqlalchemy import select
from app import db
from app.database.models import TblUsers


def login_required(f):
    """Require an authenticated user whose account still exists in the DB.

    Verifies the session contains a user_id that maps to an existing user.
    Stores the looked-up user on ``g.current_user`` for downstream access.
    Clears the session on stale user_id to avoid repeated DB misses.
    Aborts with 401 (rendered as session-expired page by the app error handler).
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            abort(401)
        user = db.session.scalar(select(TblUsers).where(TblUsers.user_id == user_id))
        if not user:
            session.clear()
            abort(401)
        g.current_user = user
        return f(*args, **kwargs)

    return decorated_function


def reviewer_required(f):
    """Require an authenticated user with reviewer role ('9').

    Delegates session validation and DB lookup to ``login_required``,
    then checks the role. ``g.current_user`` is set by ``login_required``.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.current_user.user_rolle != "9":
            abort(403)
        return f(*args, **kwargs)

    return login_required(decorated_function)
