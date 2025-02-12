import pytest
import sys
import os
from pathlib import Path
from app import create_app, db
from alembic import command
from alembic.config import Config
from app import test_config
from sqlalchemy import text
from app.demodata.filldb import insert_data_reports

@pytest.fixture(scope='session')
def app():
    # Flask-App nitialise with testconfig
    app = create_app(test_config.Config)
    with app.app_context():
        # Alembic-Migrations on testdb
        upgrade()  
        yield app 


def insert_initial_data_command():
    """Insert initial data into the table beschreibung"""

    for id, beschreibung in test_config.Config.INITIAL_DATA:
        db.session.execute(
            text(
                "INSERT INTO beschreibung (id, beschreibung) \
                VALUES (:id, :beschreibung)"
            ),
            {"id": id, "beschreibung": beschreibung},
        )
    db.session.commit()

@pytest.fixture(scope='session')
def _db(app):
    """Set up the database for the test session."""

    # create all tables in testdb
    db.create_all()  
    # fill tables
    insert_initial_data_command()
    insert_data_reports(db)
    
    yield db

    #revert all settings and remove data
    db.session.remove()
    # remove all tables after test run
    db.drop_all()


@pytest.fixture(scope='function', autouse=True)
def session(_db):
    """Erstellt eine neue Datenbank-Session für jeden Test."""
    connection = _db.engine.connect()
    transaction = connection.begin()
    options = dict(bind=connection, binds={})
    session = _db._make_scoped_session(options=options)
    _db.session = session

    yield session  # Liefere die Session für den Test

    transaction.rollback()
    connection.close()
    session.remove()


def upgrade():
    """Führe Alembic-Migrationen auf der Test-Datenbank aus."""

    connstring = 'postgresql://mantis_user:mantis@localhost/mantis_tester'
    alembic_cfg = Config('migrations/alembic.ini')
    alembic_cfg.set_main_option("sqlalchemy.url",
                                connstring)
    alembic_cfg.set_main_option("script_location", 'migrations')

    try:
        # Führe die Migrationen bis zum neuesten Stand aus
        command.upgrade(alembic_cfg, 'heads')
    except Exception as e:
        print("Fehler bei der Migration:", e)
        raise
