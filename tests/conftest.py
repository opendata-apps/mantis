import pytest
import sys
import os
from pathlib import Path
from app import create_app, db
from alembic import command
from alembic.config import Config
from app import test_config
from sqlalchemy import text
from .demodata.filldb import generate_sample_reports,  _set_gender_fields

@pytest.fixture(scope='session')
def app():
    # Flask-App mit Testkonfiguration initialisieren
    app = create_app(test_config.Config)
    with app.app_context():
        # Wende Alembic-Migrationen auf die Test-Datenbank an
        upgrade()  # Stelle sicher, dass die Migrationen angewendet werden
        yield app  # Die App für Tests bereitstellen


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
    db.create_all()  # Erstelle alle Tabellen in der Testdatenbank
    # Initiale Daten einfügen
    insert_initial_data_command()
    generate_sample_reports(app, db) # 50 Datasets 
    
    yield db
    db.session.remove()
    db.drop_all()  # Entferne alle Tabellen nach den Tests


@pytest.fixture(scope='function', autouse=True)
def session(_db):
    """Erstellt eine neue Datenbank-Session für jeden Test."""
    connection = _db.engine.connect()
    transaction = connection.begin()
    options = dict(bind=connection, binds={})
    session = _db._make_scoped_session(options=options)
    _db.session = session

    yield session  # Liefere die Session für den Test

    transaction.rollback()  # Setze die Datenbank zurück
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
