import random
from datetime import datetime

import click
from flask import Flask, render_template
from flask.cli import with_appcontext
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import text
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import Config

csrf = CSRFProtect()
db = SQLAlchemy()
migrate = Migrate()


# Define the custom command for creating the materialized view
@click.command("create-mview")
@with_appcontext
def create_materialized_view_command():
    """Create the materialized view."""
    from app.database.full_text_search import FullTextSearch
    from app.database.alldata import TblAllData

    FullTextSearch.create_materialized_view()
    TblAllData.create_materialized_view()
    click.echo("Materialized view created.")


# Define the custom command for inserting initial data
@click.command("insert-initial-data")
@with_appcontext
def insert_initial_data_command():
    """Insert initial data into the beschreibung table."""
    for id, beschreibung in Config.INITIAL_DATA:
        db.session.execute(
            text(
                "INSERT INTO beschreibung (id, beschreibung) VALUES (:id, :beschreibung)"
            ),
            {"id": id, "beschreibung": beschreibung},
        )
    db.session.commit()
    click.echo("Initial data inserted into beschreibung table.")


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    csrf.init_app(app)
    db.init_app(app)

    with app.app_context():
        app.jinja_env.filters["shuffle"] = shuffle

    migrate.init_app(app, db)

    # Register the custom command
    app.cli.add_command(create_materialized_view_command)
    app.cli.add_command(insert_initial_data_command)
    # If using Flask-App behind Nginx
    # https://flask.palletsprojects.com/en/2.3.x/deploying/proxy_fix/
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    @app.context_processor
    def inject_now():
        return {"now": datetime.utcnow()}

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


# Define the shuffle function for images
# Add the shuffle function to Jinja environment filters
def shuffle(seq):
    try:
        result = list(seq)
        random.shuffle(result)
        return result
    except:
        return seq


def page_not_found(e):
    return render_template("error/404.html"), 404


def forbidden(e):
    return render_template("error/403.html"), 403


def too_many_requests(e):
    return render_template("error/429.html"), 429
