import pytest
from app import create_app, db
from alembic import command
from alembic.config import Config
from tests.test_config import Config as TestConfig
from sqlalchemy import text
import app.database.alldata as ad
import sqlalchemy as sa
import sqlalchemy.orm as orm
from app.demodata.filldb import insert_data_reports
from app.database.populate import populate_all
from tests.database.jsondata import data as jsondata


@pytest.fixture(scope="session")
def app():
    """Create and configure a Flask app for testing.

    Creates the Flask application with test configuration and runs
    database migrations before returning the app instance.
    """
    app = create_app(TestConfig)
    with app.app_context():
        yield app


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
    """Fixture that sets up a user in the session.
    Use when you need an authenticated session."""
    from flask import session

    session["user_id"] = "9999"
    yield session


@pytest.fixture
def authenticated_client(client, session_with_user):
    """Provides a test client with an authenticated session."""
    return client


def insert_initial_data_command():
    """Insert initial data into the beschreibung table."""

    conn = TestConfig.URI
    db = sa.create_engine(conn)
    Session = orm.sessionmaker(bind=db)
    session = Session()
    for id, beschreibung in TestConfig.INITIAL_DATA:
        session.execute(
            text(
                "INSERT INTO beschreibung (id, beschreibung) VALUES (:id, :beschreibung)"
            ),
            {"id": id, "beschreibung": beschreibung},
        )
    session.commit()
    populate_all(db, session=session, vg5000_json_data=jsondata)
    insert_data_reports(session)
    ad.create_materialized_view(db, session=session)


def drop_all_with_views():
    """Drop all database tables and materialized views.

    This function ensures proper cleanup by dropping tables and views
    with CASCADE to handle dependencies correctly.
    """
    # Drop tables with CASCADE to handle dependencies correctly
    db.session.execute(text("DROP TABLE IF EXISTS public.meldungen CASCADE"))
    # Drop all remaining tables
    db.session.commit()
    db.drop_all()
    db.session.commit()


@pytest.fixture(scope="session")
def _db(app):
    """Set up the database for the test session.

    Drops everything, re-runs Alembic migrations (which create tables,
    triggers, and functions), then populates with test data.
    """
    # Setup: Drop everything and re-run migrations so triggers exist
    drop_all_with_views()
    upgrade()
    # Fill tables with test data
    insert_initial_data_command()

    yield db

    # Teardown: Run after test session completes
    db.session.remove()
    drop_all_with_views()


@pytest.fixture(scope="function", autouse=True)
def session(_db):
    """Creates a new database session for each test.

    This fixture creates a transaction for each test and rolls it back
    after the test completes, ensuring test isolation.
    """
    connection = _db.engine.connect()
    transaction = connection.begin()
    options = dict(
        bind=connection,
        binds={},
        join_transaction_mode="create_savepoint",
    )
    session = _db._make_scoped_session(options=options)
    _db.session = session

    yield session  # Provide the session for the test

    session.remove()
    transaction.rollback()
    connection.close()


def upgrade():
    """Run Alembic migrations on the test database.

    Executes all database migrations to bring the schema
    to the latest version before running tests.
    """
    import sqlalchemy as sa

    connstring = TestConfig.URI
    alembic_cfg = Config("migrations/alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", connstring)
    alembic_cfg.set_main_option("script_location", "migrations")

    # Drop alembic_version table to ensure clean migration state
    # This is necessary because test database may have inconsistent state
    # (e.g., stamped but tables not created)
    engine = sa.create_engine(connstring)
    with engine.connect() as conn:
        conn.execute(sa.text("DROP TABLE IF EXISTS alembic_version"))
        conn.commit()
    engine.dispose()

    try:
        # Execute migrations from base to latest version
        command.upgrade(alembic_cfg, "heads")
    except Exception as e:
        print("Error during migration:", e)
        raise
