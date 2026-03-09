from functools import wraps
from flask import abort, g, session
from sqlalchemy import select
from app import db
from app.database.models import TblUsers, UserRole


def load_session_user(*, require_reviewer: bool = False) -> TblUsers:
    """Load the current user from session, or abort(403).

    Verifies the session contains a user_id that maps to an existing user.
    Stores the looked-up user on ``g.current_user`` for downstream access.
    Clears the session on stale user_id to avoid repeated DB misses.

    Args:
        require_reviewer: When true, enforce reviewer role '9'.

    Returns:
        The TblUsers instance for the current session user.
    """
    user_id = session.get("user_id")
    if not user_id:
        abort(403)
    user = db.session.scalar(select(TblUsers).where(TblUsers.user_id == user_id))
    if not user:
        session.clear()
        abort(403)
    if require_reviewer and user.user_rolle != UserRole.REVIEWER:
        abort(403)
    g.current_user = user
    return user


def login_required(f):
    """Require an authenticated user whose account still exists in the DB."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        load_session_user()
        return f(*args, **kwargs)

    return decorated_function


def reviewer_required(f):
    """Require a valid reviewer session with role '9'.

    Reviewer endpoints intentionally return 403 for missing/stale sessions to
    avoid revealing authentication state.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        load_session_user(require_reviewer=True)
        return f(*args, **kwargs)

    return decorated_function
