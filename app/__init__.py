from datetime import datetime
import shutil
import os
import click
from flask import Flask, render_template, request
from flask.cli import with_appcontext
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
#from sqlalchemy.dialects.postgresql import TSVECTOR
import sqlalchemy as sa
import sqlalchemy.schema
import sqlalchemy.ext.compiler
import sqlalchemy.orm as orm
from .config import Config
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.demodata.filldb import insert_data_reports

#import create_materialized_view
csrf = CSRFProtect()
db = SQLAlchemy()
migrate = Migrate()
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    strategy="fixed-window",
    default_limits=["200 per day", "100 per hour"],
    headers_enabled=True
)


# Define the custom command for creating the materialized view
@click.command("create_all_data_view")
@with_appcontext
def create_all_data_view():
    """Create the materialized view."""
    #from app.database.full_text_search import FullTextSearch
    import  app.database.alldata as ad

    #FullTextSearch.createGen()
    ad.create_materialized_view()
    click.echo("Materialized view created.")


# @click.command("upgrade-fts")
# @with_appcontext
# def upgrade_fts_command():
#     """Upgrade the Full Text Search implementation."""
#     try:
#         # Run the migration
#         from flask import current_app
#         from flask_migrate import upgrade as flask_migrate_upgrade
        
#         with current_app.app_context():
#             # Run both migrations in sequence
#             flask_migrate_upgrade(revision='fts_upgrade_2024')
#             flask_migrate_upgrade(revision='fts_weighted_upgrade_2024')
            
#             # Refresh the view
#             from app.database.full_text_search import FullTextSearch
#             FullTextSearch.refresh_materialized_view()
        
#         click.echo("FTS upgrade completed successfully.")
#     except Exception as e:
#         click.echo(f"Error during FTS upgrade: {e}")
#         raise


# Define the custom command for inserting initial data
@click.command("insert-initial-data")
@with_appcontext
def insert_initial_data_command():
    """Insert initial data into the database using the populate script."""

    import  app.database.alldata as ad
    import  app.database.full_text_search as fts
    # Import the new populate function
    from app.database.populate import populate_all

    conn = Config.SQLALCHEMY_DATABASE_URI
    db_engine = sa.create_engine(conn) # Renamed for clarity, used by populate_all
    Session = orm.sessionmaker(bind=db_engine)
    session = Session()

    # Determine the source of VG5000 data
    if Config.TESTING:
        from tests.database.jsondata import data as jsondata
    else:
        from app.database.vg5000_gem import data as jsondata

    # Call the centralized population function
    # It handles beschreibung, feedback_types, and vg5000_aemter
    populate_all(db_engine, session, jsondata) 
    
    # Keep the creation/refresh of materialized views
    # Ensure these run *after* all initial data is potentially populated
    fts.create_materialized_view(db_engine, session=session)
    ad.create_materialized_view(db_engine, session=session)
    
    # Keep testing-specific data insertion and file operations
    if Config.TESTING:
        # Assuming insert_data_reports uses the same session
        insert_data_reports(session) 

        src = 'app/datastore/gallerie/'
        trg = 'app/datastore/2025/2025-01-19/'
        os.makedirs(os.path.dirname(trg), exist_ok=True)
        
        files=os.listdir(src)
        for fname in files:
            shutil.copy2(os.path.join(src,fname), trg)
        click.echo("Inserted test reports and copied gallery files.") # Added echo for clarity

    # No separate call to vg5000.import_aemter_data needed here anymore
    click.echo("Initial data population process finished.") # General finish message


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Simple logging configuration
    if not app.debug:
        # Production logging - log to file with rotation
        import logging
        from logging.handlers import RotatingFileHandler
        import os
        
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Set up file handler with rotation
        file_handler = RotatingFileHandler('logs/mantis.log', maxBytes=10240000, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        # Get log level from environment variable or default to INFO
        log_level = os.environ.get('FLASK_LOG_LEVEL', 'INFO').upper()
        file_handler.setLevel(log_level)
        
        # Add handlers to app logger
        app.logger.addHandler(file_handler)
        app.logger.setLevel(log_level)
        app.logger.info('Mantis tracker startup')
    
    csrf.init_app(app)
    db.init_app(app)
    limiter.init_app(app)

    migrate.init_app(app, db)

    # Register the custom commands

    app.cli.add_command(create_all_data_view)
    # app.cli.add_command(upgrade_fts_command)
    app.cli.add_command(insert_initial_data_command)

    # If using Flask-App behind Nginx
    # https://flask.palletsprojects.com/en/2.3.x/deploying/proxy_fix/
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    @app.context_processor
    def inject_now():
        return {"now": datetime.now()}

    # Import the routes
    from app.routes.admin import admin
    from app.routes.data import data
    from app.routes.main import main
    from app.routes.provider import provider
    from app.routes.statistics import stats
    from app.routes.report import report
    csrf.exempt(main)
    csrf.exempt(admin)
    csrf.exempt(stats)
    csrf.exempt(provider)

    app.register_blueprint(main)
    app.register_blueprint(admin)
    app.register_blueprint(data)
    app.register_blueprint(stats)
    app.register_blueprint(provider)
    app.register_blueprint(report)
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(403, forbidden)
    app.register_error_handler(429, too_many_requests)

    return app


def page_not_found(e):
    from flask import current_app
    current_app.logger.warning(f'Page not found: {request.url}')
    return render_template("error/404.html"), 404


def forbidden(e):
    from flask import current_app
    current_app.logger.warning(f'Forbidden access: {request.url}')
    return render_template("error/403.html"), 403


def too_many_requests(e):
    """Custom error handler for rate limiting (429 errors)"""
    from flask import current_app
    current_app.logger.warning(f'Rate limit exceeded: {request.url}')
    return render_template("error/429.html", error=e), 429
