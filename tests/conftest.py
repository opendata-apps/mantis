import pytest
from app import create_app, db
from alembic import command
from alembic.config import Config
from flask_migrate import upgrade
from app import config

@pytest.fixture(scope='session')
def app():
    # Flask-App mit Testkonfiguration initialisieren
    app = create_app(config.Config)
    with app.app_context():
        # Wende Alembic-Migrationen auf die Test-Datenbank an
        upgrade()
        yield app # Die App für Tests bereitstellen

@pytest.fixture(scope='session')
def _db(app):
    """Set up the database for the test session."""
    db.create_all() # Erstelle alle Tabellen in der Testdatenbank
    yield db
    db.session.remove()
    db.drop_all() #Entferne alle Tabellen nach den Tests

@pytest.fixture(scope='function', autouse=True)
def session(_db):
    """Erstellt eine neue Datenbank-Session für jeden Test."""
    connection = _db.engine.connect()
    transaction = connection.begin()
    options = dict(bind=connection, binds={})
    session = _db._make_scoped_session(options=options)
    _db.session = session
    yield session # Liefere die Session für den Test

    transaction.rollback() # Setze die Datenbank zurück
    connection.close()
    session.remove()

def upgrade():
    """Führe Alembic-Migrationen auf der Test-Datenbank aus."""
    alembic_cfg = Config('migrations/alembic.ini')
    alembic_cfg.set_main_option("sqlalchemy.url",
                                'postgresql://mantis_user:mantis@localhost/mantis_tester') #  Test-DB an
    alembic_cfg.set_main_option("script_location",'migrations')
    command.upgrade(alembic_cfg, 'heads')
