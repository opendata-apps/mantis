import pytest
from alembic import command
from alembic.config import Config
from flask import g
from sqlalchemy import text
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy_utils import create_database, database_exists, drop_database

from tests.helpers import set_client_user
from tests.test_config import Config as TestConfig


@pytest.fixture(scope="session", autouse=True)
def _test_database():
    """Create the test database if it doesn't exist, drop it on teardown.

    Requires CREATEDB privilege on the PostgreSQL role.
    One-time setup: ALTER USER mantis_user CREATEDB;
    """
    if not database_exists(TestConfig.URI):
        create_database(TestConfig.URI)

    yield

    drop_database(TestConfig.URI)


@pytest.fixture(scope="session")
def app(_test_database):
    """Create and configure a Flask app for testing.

    Depends on _test_database to ensure the DB exists before
    Flask-SQLAlchemy tries to connect.
    """
    from app import create_app

    app = create_app(TestConfig)

    # Tests query outside requests, so the shared app context stays open.
    # Clear Flask-Login's cached user before each request in that context.
    @app.before_request
    def _clear_cached_user():
        g.pop("_login_user", None)

    with app.app_context():
        yield app
        from app.extensions import db

        db.session.remove()
        db.engine.dispose()


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


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


# Public aliases used by tests/migrations/test_migration_chain.py
insert_initial_data_command = _seed_test_data
upgrade = _run_migrations


@pytest.fixture(scope="session")
def _db(app):
    """Set up the database for the test session.

    Resets schema, runs Alembic migrations (which create tables,
    triggers, and functions), then populates with test data.
    """
    from app.extensions import db

    _reset_schema()
    _run_migrations()
    _seed_test_data()

    yield db


@pytest.fixture(scope="function", autouse=True)
def session(_db):
    """Isolate each test, including application commits and rollbacks."""
    # Closing the connection rolls back the outer transaction.
    with _db.engine.connect() as connection:
        connection.begin()
        original_session = _db.session
        session = scoped_session(
            sessionmaker(bind=connection, join_transaction_mode="create_savepoint"),
            scopefunc=original_session.registry.scopefunc,
        )
        _db.session = session

        try:
            yield session
        finally:
            _db.session = original_session
            session.remove()
