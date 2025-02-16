import pytest
import sys
import os
from pathlib import Path
from app import create_app, db
from alembic import command
from alembic.config import Config
from app.test_config import Config as TestConfig
from sqlalchemy import text
#from app.demodata.filldb import insert_data_reports
#from app import insert_initial_data_command
import  app.database.full_text_search as fts
import sqlalchemy as sa
import sqlalchemy.orm as orm
from app.demodata.filldb import insert_data_reports

@pytest.fixture(scope='session')
def app():
    # Flask-App nitialise with testconfig
    app = create_app(TestConfig)
    with app.app_context():
        # Alembic-Migrations on testdb
        upgrade()  
        yield app 

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


def drop_all_with_views():
    # Alle Materialized Views löschen (mit CASCADE)
    db.session.execute(text(
        'DROP TABLE IF EXISTS public.meldungen CASCADE'
    ))

    db.session.execute(text(
        'DROP MATERIALIZED VIEW IF EXISTS public.full_text_search CASCADE'
    ))
    # Jetzt alle Tabellen löschen
    db.session.commit()
    db.drop_all()
    db.session.commit()
    
    
@pytest.fixture(scope='session')
def _db(app):
    """Set up the database for the test session."""

    # create all tables in testdb

    # Test-Setup: Vor jedem Testlauf aufrufen
    drop_all_with_views()
    db.create_all()  
    # fill tables
    insert_initial_data_command()
        
    yield db

    db.session.remove()
    # remove all tables after test run
    drop_all_with_views()


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
