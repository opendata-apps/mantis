import pytest
from app import create_app, db
from alembic import command
from alembic.config import Config
from app.test_config import Config as TestConfig
from sqlalchemy import text
import  app.database.full_text_search as fts
import  app.database.alldata as ad
import sqlalchemy as sa
import sqlalchemy.orm as orm
from app.demodata.filldb import insert_data_reports

@pytest.fixture(scope='session')
def app():
    """Create and configure a Flask app for testing.
    
    Creates the Flask application with test configuration and runs
    database migrations before returning the app instance.
    """
    app = create_app(TestConfig)
    with app.app_context():
        # Run Alembic migrations on test database
        upgrade()  
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
    session['user_id'] = '9999'
    yield session

@pytest.fixture
def mock_request(app, session_with_user):
    """Creates a mock request object with session data.
    Use for testing routes that access request data."""
    from werkzeug.test import EnvironBuilder
    from werkzeug.wrappers import Request
    from flask import session as flask_session
    
    # Create environment with form data
    builder = EnvironBuilder(
        method='POST',
        data={'user_id': '9999'}
    )
    
    # Create the request object
    request = Request(builder.get_environ())
    
    # Make sure the request has access to the session
    request.environ['flask.session'] = flask_session
    
    yield request

@pytest.fixture
def mock_render_template():
    """Provides a mock for Flask's render_template function.
    
    Example usage:
        def test_some_route(mock_render_template):
            # Make request to endpoint
            response = client.get('/')
            
            # Assert render_template was called with correct template and context
            mock_render_template.assert_called_once_with('home.html', user=None)
    """
    from unittest.mock import patch
    with patch('flask.render_template') as mock:
        mock.return_value = ''
        yield mock

@pytest.fixture
def authenticated_client(client, session_with_user):
    """Provides a test client with an authenticated session."""
    return client

@pytest.fixture
def form_data_request(mock_request, request):
    """Generic fixture for mocking a request with form data.
    
    Usage:
        @pytest.fixture
        def my_form_data(form_data_request):
            form_data_request.form = {
                'field1': 'value1',
                'field2': 'value2'
            }
            return form_data_request
    """
    # Get form data from test markers if provided
    marker = request.node.get_closest_marker("form_data")
    form_data = marker.args[0] if marker else {}
    
    # Add form data to the mock request
    mock_request.form = form_data
    return mock_request

@pytest.fixture
def form_with_dates(form_data_request):
    """Fixture for mocking a request with standard date range form data.
    Commonly used in statistics tests."""
    form_data_request.form = {
        'dateFrom': '2024-01-01',
        'dateTo': '2025-12-31',
        'user_id': '9999'
    }
    return form_data_request

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

    insert_data_reports(session)
    fts.create_materialized_view(db, session=session)
    ad.create_materialized_view(db, session=session)
    
    
def drop_all_with_views():
    """Drop all database tables and materialized views.
    
    This function ensures proper cleanup by dropping tables and views
    with CASCADE to handle dependencies correctly.
    """
    # Drop all materialized views with CASCADE
    db.session.execute(text(
        'DROP TABLE IF EXISTS public.meldungen CASCADE'
    ))

    db.session.execute(text(
        'DROP MATERIALIZED VIEW IF EXISTS public.full_text_search CASCADE'
    ))
    # Drop all remaining tables
    db.session.commit()
    db.drop_all()
    db.session.commit()
    
    
@pytest.fixture(scope='session')
def _db(app):
    """Set up the database for the test session.
    
    Creates all database tables, populates with initial test data,
    and handles cleanup after all tests are complete.
    """
    # Setup: Run before test session begins
    drop_all_with_views()
    db.create_all()  
    # Fill tables with test data
    insert_initial_data_command()
        
    yield db

    # Teardown: Run after test session completes
    db.session.remove()
    drop_all_with_views()


@pytest.fixture(scope='function', autouse=True)
def session(_db):
    """Creates a new database session for each test.
    
    This fixture creates a transaction for each test and rolls it back
    after the test completes, ensuring test isolation.
    """
    connection = _db.engine.connect()
    transaction = connection.begin()
    options = dict(bind=connection, binds={})
    session = _db._make_scoped_session(options=options)
    _db.session = session

    yield session  # Provide the session for the test

    transaction.rollback()
    connection.close()
    session.remove()


def upgrade():
    """Run Alembic migrations on the test database.
    
    Executes all database migrations to bring the schema
    to the latest version before running tests.
    """
    connstring = 'postgresql://mantis_user:mantis@localhost/mantis_tester'
    alembic_cfg = Config('migrations/alembic.ini')
    alembic_cfg.set_main_option("sqlalchemy.url",
                                connstring)
    alembic_cfg.set_main_option("script_location", 'migrations')

    try:
        # Execute migrations to the latest version
        command.upgrade(alembic_cfg, 'heads')
    except Exception as e:
        print("Error during migration:", e)
        raise
