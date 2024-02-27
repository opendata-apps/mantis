from functools import wraps
from flask import abort, session


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            abort(403)
        return f(*args, **kwargs)

    return decorated_function
