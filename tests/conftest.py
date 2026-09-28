import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, make_url, text
from sqlalchemy.orm import Session
from sqlalchemy_utils import create_database, database_exists, drop_database

from tests.helpers import set_client_user
from tests.test_config import Config as TestConfig

# Arbitrary, only has to be the same number in every run of this suite.
_RUN_LOCK_KEY = 7_307_195_812_240_001


@pytest.fixture(scope="session")
def _exclusive_run():
    """Refuse to start while another run already owns the test databases.

    The databases are shared mutable state: a second writer surfaces as
    deadlocks, duplicate keys and vanished tables in unrelated tests, hundreds
    of tests after the actual cause. The lock lives on the maintenance
    database so it does not block dropping the test ones.
    """
    engine = create_engine(make_url(TestConfig.URI).set(database="postgres"))
    with engine.connect() as guard:
        held = guard.scalar(
            text("SELECT pg_try_advisory_lock(:key)"), {"key": _RUN_LOCK_KEY}
        )
        if not held:
            # Ends the session here: as a fixture failure this would repeat
            # itself for every database test instead of saying it once.
            pytest.exit(
                f"Another test run already owns {TestConfig.DATABASE_DB}. "
                "Wait for it to finish — a second run corrupts both.",
                returncode=2,
            )
        yield
    engine.dispose()


@pytest.fixture(scope="session")
def _test_database(_exclusive_run):
    """Create the test database if it doesn't exist, drop it on teardown.

    Requires CREATEDB privilege on the PostgreSQL role.
    One-time setup: ALTER USER mantis_user CREATEDB;
    """
    if not database_exists(TestConfig.URI):
        create_database(TestConfig.URI)

    yield

    drop_database(TestConfig.URI)


@pytest.fixture
def config_base():
    """The configuration the per-test config derives from.

    ``tests/migrations`` overrides this to point at its own database.
    """
    return TestConfig


@pytest.fixture
def test_config(tmp_path, tmp_path_factory, config_base):
    class Config(config_base):
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


def _truncate_all(tables: tuple[str, ...]):
    """Empty every seeded table and rewind its identity counter.

    CASCADE covers the foreign keys between them; RESTART IDENTITY makes the
    ids that ``_seed_test_data`` hands out the same in every test.
    """
    from app.extensions import db

    quote = db.engine.dialect.identifier_preparer.quote
    names = ", ".join(f"public.{quote(table)}" for table in tables)
    db.session.execute(text(f"TRUNCATE TABLE {names} RESTART IDENTITY CASCADE"))
    db.session.commit()


def _seed_test_data():
    """Populate test database with initial + demo data."""
    from app.extensions import db
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


def _run_migrations():
    """Run Alembic migrations on the test database."""
    alembic_cfg = Config("migrations/alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", TestConfig.URI)
    alembic_cfg.set_main_option("script_location", "migrations")
    command.upgrade(alembic_cfg, "heads")


@pytest.fixture(scope="session")
def _schema(_test_database):
    """Migrate once per test run; returns the tables ``_db`` empties per test.

    ``tests/migrations`` replays the chain itself and does so against its own
    database, so nothing removes this schema while tests run.
    """
    from app import create_app

    app = create_app(TestConfig)
    with app.app_context():
        from app.extensions import db

        _reset_schema()
        _run_migrations()
        tables = tuple(
            db.session.scalars(
                text(
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public' "
                    "AND tablename <> 'alembic_version'"
                )
            )
        )
        # Release the connection too, or the session-end DROP DATABASE finds
        # this one still attached.
        db.session.remove()
        db.engine.dispose()

    assert tables, "migrations created no tables"
    return tables


@pytest.fixture
def _db(app, _schema):
    """Restore the seeded starting state before each test that uses it.

    Tests commit for real — an HTTP or CLI call runs on its own connection —
    so isolation comes from emptying the tables, not from a rollback.
    """
    from app.extensions import db

    with app.app_context():
        _truncate_all(_schema)
        _seed_test_data()

    return db


@pytest.fixture
def session(_db, app):
    """Use a separate session for test setup and saved-result assertions."""
    with app.app_context():
        engine = _db.engine

    with Session(engine) as session:
        yield session
