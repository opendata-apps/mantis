from datetime import datetime
import shutil
import os
import click
from flask import Flask, jsonify, render_template, request
from flask.cli import with_appcontext
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_favicon import FlaskFavicon
from werkzeug.middleware.proxy_fix import ProxyFix
import sqlalchemy as sa
import sqlalchemy.schema
import sqlalchemy.ext.compiler
import sqlalchemy.orm as orm
from .config import Config
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

csrf = CSRFProtect()
db = SQLAlchemy()
migrate = Migrate()
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    strategy="fixed-window",
    default_limits=["200 per day", "100 per hour"],
    headers_enabled=True,
)
mail = Mail()
flaskFavicon = FlaskFavicon()


# Define the custom command for creating the materialized view
@click.command("create_all_data_view")
@with_appcontext
def create_all_data_view():
    """Create the materialized view."""
    import app.database.alldata as ad
    import app.database.full_text_search as fts

    conn = Config.SQLALCHEMY_DATABASE_URI
    # Renamed for clarity, used by populate_all
    db_engine = sa.create_engine(conn)
    Session = orm.sessionmaker(bind=db_engine)
    session = Session()

    ad.create_materialized_view(db_engine, session=session)
    fts.create_materialized_view(db_engine, session=session)
    click.echo("Materialized views created.")


@click.command("seed")
@click.option("--demo", is_flag=True, help="Include demo reports and images")
@with_appcontext
def seed_command(demo):
    """Seed database with base data. Use --demo to include sample reports."""
    import app.database.alldata as ad
    import app.database.full_text_search as fts
    from app.database.populate import populate_all
    from app.database.vg5000_gem import data as jsondata

    db_engine = sa.create_engine(Config.SQLALCHEMY_DATABASE_URI)
    session = orm.sessionmaker(bind=db_engine)()

    # Always populate base data (idempotent)
    populate_all(db_engine, session, jsondata)
    click.echo("Base data seeded.")

    if demo:
        from app.demodata.filldb import insert_data_reports

        insert_data_reports(session)
        _copy_demo_images()
        click.echo("Demo data seeded.")

    # Refresh views
    from app import db as flask_db

    ad.refresh_materialized_view(flask_db)
    fts.refresh_materialized_view(flask_db)
    click.echo("Done.")


def _copy_demo_images():
    """Copy demo images for sample reports."""
    from app.config import Config

    # Source: demodata folder (tracked in git, not publicly served)
    src = os.path.join(os.path.dirname(__file__), "demodata", "images")
    # Target: user uploads folder for demo reports
    trg = os.path.join(Config.UPLOAD_FOLDER, "2025", "2025-01-19")
    os.makedirs(trg, exist_ok=True)
    mappings = [
        ("mantis1.webp", "Zossen-20250119100000-9999.webp"),
        (
            "mantis2.webp",
            "Ziesar-20250119101500-f04ad4e0b099b6404b1ccda0af0282cf49693b43.webp",
        ),
        (
            "mantis3.webp",
            "Cottbus-20250119103000-5843c1093f94be44442ff876cac6185a2d36310e.webp",
        ),
        (
            "mantis4.webp",
            "Treuenbrietzen-20250119104500-264aca7e20e15aa2401f042dceed384da6d7747a.webp",
        ),
        (
            "mantis5.webp",
            "Pritzwalk-20250119110000-2ab71517482f824f925d09b9aa6e387df99befa7.webp",
        ),
        (
            "mantis6.webp",
            "Halle_Saale-20250119111500-874208b1da349f20a88862f38a856bd711c2e165.webp",
        ),
        (
            "mantis1.webp",
            "Fichtwald-20250119113000-1fb0cfb0be3b0c75c537a50c57e0060ba8b6837e.webp",
        ),
        (
            "mantis2.webp",
            "Luckenwalde-20250119114500-c56fe0b6262dc626a5faf21c55b1f34f7babcfb1.webp",
        ),
        (
            "mantis3.webp",
            "Cottbus-20250119120000-2d7345fd039eaef8796047c61ab760cac52b67e4.webp",
        ),
        (
            "mantis4.webp",
            "Bad_Freienwalde_Oder-20250119121500-9b9d6a941dea27e46f4e5c79284f7df4c82fca49.webp",
        ),
        (
            "mantis5.webp",
            "Berlin-20250119123000-a88de66aa7976cb7990af54c16c0fd2c067515f9.webp",
        ),
        (
            "mantis6.webp",
            "Frankfurt_Oder-20250119124500-d2c830fd84ccabe149aff154c5e1ddcef662f052.webp",
        ),
        (
            "mantis5.webp",
            "Caputh-20250119130000-0c7571741c04d2365aa7816efd298e8df9091122.webp",
        ),
        (
            "mantis2.webp",
            "Seevetal-20250119131500-166bc2da77cb1d6e9a07f3d6fd61c841b394f3c6.webp",
        ),
        (
            "mantis3.webp",
            "Leipzig-20250119133000-6325e4e69ee6789a7aa0ebb9a0e0b63cdf67795a.webp",
        ),
        (
            "mantis4.webp",
            "Berlin-20250119134500-086cd63464247668799cc5a508235012b64a4bf9.webp",
        ),
        (
            "mantis5.webp",
            "Elsterwerda-20250119140000-a1a0c14a53b7bbd010fc48ab2ac42d35d959d2b8.webp",
        ),
        (
            "mantis6.webp",
            "Jueterbog-20250119141500-5f4a7fec84fb0801a5157cf1ce41835774a92704.webp",
        ),
        (
            "mantis1.webp",
            "Jessen_Elster-20250119143000-7228ef93c5b4347ffdcfe63d77bd8617fdb080e5.webp",
        ),
        (
            "mantis2.webp",
            "Friesack-20250119144500-c56782d029b8a62160175fd7112b74f573cd101f.webp",
        ),
    ]
    for src_file, target_file in mappings:
        src_path = os.path.join(src, src_file)
        if os.path.exists(src_path):
            shutil.copy2(src_path, os.path.join(trg, target_file))


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    mail.init_app(app)

    # Simple logging configuration
    if not app.debug:
        # Production logging - log to file with rotation
        import logging
        from logging.handlers import RotatingFileHandler
        import os

        # Create logs directory if it doesn't exist
        if not os.path.exists("logs"):
            os.mkdir("logs")

        # Set up file handler with rotation
        file_handler = RotatingFileHandler(
            "logs/mantis.log", maxBytes=10240000, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
            )
        )

        # Get log level from environment variable or default to INFO
        log_level = os.environ.get("FLASK_LOG_LEVEL", "INFO").upper()
        file_handler.setLevel(log_level)

        app.logger.addHandler(file_handler)
        app.logger.setLevel(log_level)
        app.logger.info("Mantis tracker startup")

    csrf.init_app(app)
    db.init_app(app)
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

    # Register CLI commands
    app.cli.add_command(create_all_data_view)
    app.cli.add_command(seed_command)

    # If using Flask-App behind Nginx
    # https://flask.palletsprojects.com/en/2.3.x/deploying/proxy_fix/
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

    # Import the routes
    from app.routes.admin import admin
    from app.routes.data import data
    from app.routes.main import main
    from app.routes.provider import provider
    from app.routes.statistics import stats
    from app.routes.report import report

    # CSRF exemption for stats: templates lack CSRF tokens (TODO: fix and remove)
    csrf.exempt(stats)

    app.register_blueprint(main)
    app.register_blueprint(admin)
    app.register_blueprint(data)
    app.register_blueprint(stats)
    app.register_blueprint(provider)
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
        # Log the exception
        app.logger.exception(f"Unhandled exception: {str(e)}")

        # Return 500 error for unhandled exceptions
        if app.debug:
            raise e  # Re-raise in debug mode
        return render_template("error/500.html"), 500

    return app


def wants_json_response():
    """Check if the client prefers a JSON response (AJAX/API calls)."""
    best = request.accept_mimetypes.best_match(["application/json", "text/html"])
    return (
        best == "application/json"
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
    )


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
