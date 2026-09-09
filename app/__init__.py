"""Main application package.

Binds nothing but ``create_app``, so ``from app import db`` raises ImportError
instead of becoming a second path to ``app.extensions``.
"""

from app.factory import create_app

__all__ = ["create_app"]
