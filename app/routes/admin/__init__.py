"""Admin area: reviewer workflow, Excel export, and the alldata table browser.

Importing the route modules is what registers their routes on the blueprint, so
the imports below are deliberately unused.
"""

from app.routes.admin.blueprint import admin
from app.routes.admin import database, export, reviewer  # noqa: F401

__all__ = ["admin"]
