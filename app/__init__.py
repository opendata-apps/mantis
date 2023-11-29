import click
from flask.cli import with_appcontext
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from flask_migrate import Migrate
from .config import Config
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
from flask import render_template
import random


csrf = CSRFProtect()
db = SQLAlchemy()
migrate = Migrate()


# Define the custom command for creating the materialized view
@click.command('create-mview')
@with_appcontext
def create_materialized_view_command():
    """Create the materialized view."""
    from app.database.full_text_search import FullTextSearch
    FullTextSearch.create_materialized_view()
    click.echo('Materialized view created.')


@click.command('insert-initial-data')
@with_appcontext
def insert_initial_data_command():
    """Insert initial data into the beschreibung table."""
    initial_data = [
        (1, 'Im Haus'),
        (2, 'Im Garten'),
        (3, 'Auf dem Balkon/auf der Terrasse'),
        (4, 'Am Fenster/an der Hauswand'),
        (5, 'Industriebrache'),
        (6, 'Im Wald'),
        (7, 'Wiese/Weide'),
        (8, 'Heidelandschaft'),
        (9, 'Straßengraben/Wegesrand/Ruderalflur'),
        (10, 'Gewerbegebiet'),
        (11, 'Im oder am Auto'),
        (99, 'Anderer Fundort')
    ]

    for id, beschreibung in initial_data:
        db.session.execute(
            text("INSERT INTO beschreibung (id, beschreibung) VALUES (:id, :beschreibung)"),
            {'id': id, 'beschreibung': beschreibung}
        )
    db.session.commit()
    click.echo('Initial data inserted into beschreibung table.')

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    csrf.init_app(app)
    db.init_app(app)

    with app.app_context():
        app.jinja_env.filters['shuffle'] = shuffle

    migrate.init_app(app, db)

    # Register the custom command
    app.cli.add_command(create_materialized_view_command)
    app.cli.add_command(insert_initial_data_command)
    # If using Flask-App behind Nginx
    # https://flask.palletsprojects.com/en/2.3.x/deploying/proxy_fix/
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1,
                            x_proto=1, x_host=1, x_prefix=1)

    from app.routes.main import main
    from app.routes.admin import admin
    from app.routes.data import data
    from app.routes.reviewer import review
    from app.routes.provider import provider
    from app.routes.statistics import stats

    csrf.exempt(main)
    csrf.exempt(admin)
    csrf.exempt(review)
    csrf.exempt(provider)
    csrf.exempt(stats)

    app.register_blueprint(main)
    app.register_blueprint(admin)
    app.register_blueprint(data)
    app.register_blueprint(review)
    app.register_blueprint(provider)
    app.register_blueprint(stats)
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(403, forbidden)
    app.register_error_handler(429, too_many_requests)

    return app


# Define the shuffle function
def shuffle(seq):
    try:
        result = list(seq)
        random.shuffle(result)
        return result
    except:
        return seq


# Add the shuffle function to Jinja environment filters


def page_not_found(e):
    return render_template("error/404.html"), 404


def forbidden(e):
    return render_template("error/403.html"), 403


def too_many_requests(e):
    return render_template("error/429.html"), 429
