"""Fixtures for Alembic migration chain tests.

Overrides the parent conftest's autouse ``session`` fixture so that
migration tests manage their own database state via Alembic commands
instead of the regular transactional-rollback strategy.
"""

import pytest
import sqlalchemy as sa
from alembic.config import Config

from tests.test_config import Config as TestConfig


@pytest.fixture(autouse=True)
def session():
    """Override parent's autouse session — migration tests manage DB state directly."""
    yield


@pytest.fixture
def alembic_config(app):
    """Alembic config bound to the test database.

    Depends on the parent conftest's ``app`` fixture so that env.py
    can resolve ``current_app`` when Alembic runs migrations.
    """
    cfg = Config("migrations/alembic.ini")
    cfg.set_main_option("sqlalchemy.url", TestConfig.URI)
    cfg.set_main_option("script_location", "migrations")
    return cfg


@pytest.fixture
def clean_db():
    """Reset the test database to a completely empty state.

    Uses ``DROP SCHEMA public CASCADE`` to remove all tables, views,
    functions, triggers, types, and sequences — ensuring a pristine
    starting point for migration chain tests.
    """
    engine = sa.create_engine(TestConfig.URI)
    with engine.connect() as conn:
        conn.execute(sa.text("DROP SCHEMA public CASCADE"))
        conn.execute(sa.text("CREATE SCHEMA public"))
        conn.commit()
    engine.dispose()
