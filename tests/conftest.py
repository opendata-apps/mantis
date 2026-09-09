import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy_utils import create_database, database_exists, drop_database

from tests.helpers import set_client_user
from tests.test_config import Config as TestConfig


@pytest.fixture(scope="session")
def _test_database():
    """Create the test database if it doesn't exist, drop it on teardown.

    Requires CREATEDB privilege on the PostgreSQL role.
    One-time setup: ALTER USER mantis_user CREATEDB;
    """
    if not database_exists(TestConfig.URI):
        create_database(TestConfig.URI)

    yield

    drop_database(TestConfig.URI)


@pytest.fixture
def test_config(tmp_path, tmp_path_factory):
    class Config(TestConfig):
        UPLOAD_FOLDER = str(tmp_path / "uploads")
        BACKUP_DIR = str(tmp_path / "backups")
        FAVICON_BUILD_DIR = str(tmp_path_factory.getbasetemp() / "favicons")

    return Config


@pytest.fixture
def app(_test_database, test_config):
    """Create and configure a Flask app for testing.

    Depends on _test_database to ensure the DB exists before
    Flask-SQLAlchemy tries to connect.
    """
    from app import create_app

    app = create_app(test_config)

    yield app
    with app.app_context():
        from app.extensions import db

        db.engine.dispose()


@pytest.fixture
def client(app, _db):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture
def app_ctx(app):
    """Provide a context for direct calls to application helpers."""
    with app.app_context():
        yield


@pytest.fixture
def request_context(app):
    """Provides a Flask request context for tests.
    Use this when you need to access Flask's request, session, or g objects."""
    with app.test_request_context() as ctx:
        yield ctx


@pytest.fixture
def session_with_user(request_context):
    """Fixture that sets up a user in the Flask request context session.

    Use when testing functions that read session directly (e.g. statistics
    helpers called outside the test client). For test-client authentication
    use ``authenticated_client`` instead.
    """
    from flask import session

    session["_user_id"] = "9999"
    session["_fresh"] = True
    yield session


@pytest.fixture
def authenticated_client(client):
    """Provides a test client with an authenticated reviewer session.

    Uses ``client.session_transaction()`` — the correct way to populate
    the cookie-backed session used by the Flask test client.
    """
    return set_client_user(client, "9999")


def _reset_schema():
    """Reset the test database to a completely empty state.

    Uses DROP SCHEMA public CASCADE to remove all tables, views,
    functions, triggers, types, and sequences at once.
    """
    from app.extensions import db

    db.session.execute(text("DROP SCHEMA public CASCADE"))
    db.session.execute(text("CREATE SCHEMA public"))
    db.session.commit()


def _seed_test_data():
    """Populate test database with initial + demo data."""
    from app.extensions import db
    import app.database.alldata as ad
    from app.demodata.filldb import insert_data_reports
    from app.database.populate import populate_all
    from tests.database.jsondata import data as jsondata

    session = db.session
    for id, beschreibung in TestConfig.INITIAL_DATA:
        session.execute(
            text(
                "INSERT INTO beschreibung (id, beschreibung) "
                "VALUES (:id, :beschreibung)"
            ),
            {"id": id, "beschreibung": beschreibung},
        )
    session.commit()
    populate_all(session=session, vg5000_json_data=jsondata)
    insert_data_reports(session)
    ad.create_materialized_view(db.engine, session=session)


def _run_migrations():
    """Run Alembic migrations on the test database."""
    alembic_cfg = Config("migrations/alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", TestConfig.URI)
    alembic_cfg.set_main_option("script_location", "migrations")
    command.upgrade(alembic_cfg, "heads")


@pytest.fixture
def _db(app):
    """Rebuild the database before each test that uses it.

    Resets schema, runs Alembic migrations (which create tables,
    triggers, and functions), then populates with test data.
    """
    from app.extensions import db

    with app.app_context():
        _reset_schema()
        _run_migrations()
        _seed_test_data()

    return db


@pytest.fixture
def session(_db, app):
    """Use a separate session for test setup and saved-result assertions."""
    with app.app_context():
        engine = _db.engine

    with Session(engine) as session:
        yield session
