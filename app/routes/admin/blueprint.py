"""The admin blueprint on its own, so the route modules can import it without
importing each other."""

from flask import Blueprint

admin = Blueprint("admin", __name__)
