from functools import wraps
from flask import abort, session
from sqlalchemy import select
from app import db
from app.database.models import TblUsers


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


def reviewer_required(f):
    """Require an authenticated user with reviewer role ('9')."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get("user_id")
        if not user_id:
            abort(403)
        user = db.session.scalar(select(TblUsers).where(TblUsers.user_id == user_id))
        if not user or user.user_rolle != "9":
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
