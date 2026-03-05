from datetime import datetime
import os
from flask import Flask, jsonify, render_template, request
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_favicon import FlaskFavicon
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix
from .config import Config
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

csrf = CSRFProtect()
db = SQLAlchemy()
migrate = Migrate()
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
    strategy="fixed-window",
    default_limits=["200 per day", "100 per hour"],
    headers_enabled=True,
)
mail = Mail()
flaskFavicon = FlaskFavicon()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Logging first — so all init_app calls can log properly
    if not app.debug:
        import logging
        from logging.handlers import RotatingFileHandler

        if not os.path.exists("logs"):
            os.mkdir("logs")

        file_handler = RotatingFileHandler(
            "logs/mantis.log", maxBytes=10240000, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )

        log_level = os.environ.get("FLASK_LOG_LEVEL", "INFO").upper()
        file_handler.setLevel(log_level)

        app.logger.addHandler(file_handler)
        app.logger.setLevel(log_level)
        app.logger.info("Mantis tracker startup")

    # Extensions
    csrf.init_app(app)
    db.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    flaskFavicon.init_app(app)

    # Register favicons
    flaskFavicon.register_favicon("app/static/images/logo.png", "default")
    # You can register additional favicons for different sections
    # For example, a special one for admin pages:
    # flaskFavicon.register_favicon('app/static/images/admin-logo.png', 'admin')

    migrate.init_app(app, db)

    # Initialize Vite asset helper
    from app.tools import vite

    vite.init_app(app)

    # Heroicons Jinja globals — usage: {{ heroicon_outline("map-pin", class="w-4 h-4") }}
    from heroicons.jinja import (
        heroicon_micro,
        heroicon_mini,
        heroicon_outline,
        heroicon_solid,
    )

    app.jinja_env.globals.update(
        {
            "heroicon_micro": heroicon_micro,
            "heroicon_mini": heroicon_mini,
            "heroicon_outline": heroicon_outline,
            "heroicon_solid": heroicon_solid,
        }
    )

    # Register CLI commands
    from app.cli import register_commands

    register_commands(app)

    @app.shell_context_processor
    def make_shell_context():
        from app.database.models import TblMeldungen, TblUsers, TblFundorte

        return {
            "db": db,
            "TblMeldungen": TblMeldungen,
            "TblUsers": TblUsers,
            "TblFundorte": TblFundorte,
        }

    # Only apply ProxyFix when behind a reverse proxy (e.g. Nginx).
    # Applying unconditionally lets clients forge X-Forwarded-For headers.
    # https://flask.palletsprojects.com/en/stable/deploying/proxy_fix/
    if not app.debug:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    @app.context_processor
    def inject_now():
        return {"now": datetime.now()}

    # Security headers middleware
    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        if app.config.get("PREFERRED_URL_SCHEME") == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response

    # HTMX error recovery middleware
    # When an HTMX request hits an auth/CSRF denial, the default HTMX 2.0
    # behavior (swap:false for 4xx) causes silent failure — the user gets
    # no feedback. Adding HX-Redirect tells HTMX to do a full-page
    # navigation to a recovery URL instead.
    # Pattern: https://www.wimdeblauwe.com/blog/2022/10/04/htmx-authentication-error-handling/
    @app.after_request
    def htmx_error_redirect(response):
        if request.headers.get("HX-Request") == "true" and response.status_code == 403:
            response.headers["HX-Redirect"] = "/"
        return response

    # Import the routes
    from app.routes.admin import admin
    from app.routes.data import data
    from app.routes.main import main
    from app.routes.provider import provider
    from app.routes.statistics import stats
    from app.routes.regionen import regionen
    from app.routes.report import report

    app.register_blueprint(main)
    app.register_blueprint(admin)
    app.register_blueprint(data)
    app.register_blueprint(stats)
    app.register_blueprint(provider)
    app.register_blueprint(regionen)
    app.register_blueprint(report)
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(403, forbidden)
    app.register_error_handler(429, too_many_requests)
    app.register_error_handler(500, internal_server_error)

    # Exempt admin blueprint from rate limiting
    limiter.exempt(admin)
    # CSRF error handler
    from flask_wtf.csrf import CSRFError

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        app.logger.warning(f"CSRF error: {str(e)}")
        return render_template("error/403.html"), 403

    # Global exception handler
    @app.errorhandler(Exception)
    def handle_exception(e):
        # Pass through HTTP errors with their correct status codes
        if isinstance(e, HTTPException):
            return e

        app.logger.exception(f"Unhandled exception: {str(e)}")

        if app.debug:
            raise e
        return render_template("error/500.html"), 500

    return app


def wants_json_response():
    """Check if the client prefers a JSON response (AJAX/API calls)."""
    best = request.accept_mimetypes.best_match(["application/json", "text/html"])
    return best == "application/json"


def page_not_found(e):
    from flask import current_app

    current_app.logger.warning(
        f"Page not found: {request.url} - User Agent: {request.headers.get('User-Agent', 'Unknown')}"
    )
    if wants_json_response():
        return jsonify({"error": e.description or "Not found"}), 404
    return render_template("error/404.html"), 404


def forbidden(e):
    from flask import current_app

    current_app.logger.warning(
        f"Forbidden access: {request.url} - User Agent: {request.headers.get('User-Agent', 'Unknown')}"
    )
    if wants_json_response():
        return jsonify({"error": e.description or "Forbidden"}), 403
    return render_template("error/403.html"), 403


def too_many_requests(e):
    """Custom error handler for rate limiting (429 errors)"""
    from flask import current_app

    current_app.logger.warning(
        f"Rate limit exceeded: {request.url} - User Agent: {request.headers.get('User-Agent', 'Unknown')}"
    )
    if wants_json_response():
        return jsonify({"error": e.description or "Too many requests"}), 429
    return render_template("error/429.html", error=e), 429


def internal_server_error(e):
    from flask import current_app

    current_app.logger.error(f"Internal server error: {request.url} - Error: {str(e)}")
    if wants_json_response():
        return jsonify({"error": "Internal server error"}), 500
    return render_template("error/500.html"), 500
