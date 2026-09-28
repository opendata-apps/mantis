"""Fixtures for migration tests that manage database state through Alembic."""

import pytest
import sqlalchemy as sa
from alembic.config import Config
from sqlalchemy_utils import create_database, database_exists, drop_database

from tests.test_config import MigrationsConfig


@pytest.fixture(scope="session")
def _migrations_database(_exclusive_run):
    """Create the migrations-only database, drop it on teardown."""
    if not database_exists(MigrationsConfig.URI):
        create_database(MigrationsConfig.URI)

    yield

    drop_database(MigrationsConfig.URI)


@pytest.fixture
def config_base(_migrations_database):
    """Point the parent conftest's ``app`` at the migrations database."""
    return MigrationsConfig


@pytest.fixture
def alembic_config(app):
    """Alembic config bound to the migrations database.

    Depends on the parent conftest's ``app`` fixture so that env.py
    can resolve ``current_app`` when Alembic runs migrations.
    """
    cfg = Config("migrations/alembic.ini")
    cfg.set_main_option("sqlalchemy.url", MigrationsConfig.URI)
    cfg.set_main_option("script_location", "migrations")
    return cfg


@pytest.fixture
def clean_db(_migrations_database):
    """Reset the migrations database to a completely empty state.

    Uses ``DROP SCHEMA public CASCADE`` to remove all tables, views,
    functions, triggers, types, and sequences — ensuring a pristine
    starting point for migration chain tests.
    """
    engine = sa.create_engine(MigrationsConfig.URI)
    with engine.connect() as conn:
        conn.execute(sa.text("DROP SCHEMA public CASCADE"))
        conn.execute(sa.text("CREATE SCHEMA public"))
        conn.commit()
    engine.dispose()
