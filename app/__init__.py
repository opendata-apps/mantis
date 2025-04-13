from datetime import datetime, timezone
import shutil
import os
import click
from flask import Flask, render_template
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
from sqlalchemy import text
from .config import Config

from app.demodata.filldb import insert_data_reports

#import create_materialized_view
csrf = CSRFProtect()
db = SQLAlchemy()
migrate = Migrate()


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
    csrf.init_app(app)
    db.init_app(app)

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
        return {"now": datetime.now(timezone.utc)}

    # Import the routes
    from app.routes.admin import admin
    from app.routes.data import data
    from app.routes.main import main
    from app.routes.provider import provider
    from app.routes.statistics import stats

    csrf.exempt(main)
    csrf.exempt(admin)
    csrf.exempt(stats)
    csrf.exempt(provider)

    app.register_blueprint(main)
    app.register_blueprint(admin)
    app.register_blueprint(data)
    app.register_blueprint(stats)
    app.register_blueprint(provider)
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(403, forbidden)
    app.register_error_handler(429, too_many_requests)

    return app


def page_not_found(e):
    return render_template("error/404.html"), 404


def forbidden(e):
    return render_template("error/403.html"), 403


def too_many_requests(e):
    return render_template("error/429.html"), 429
