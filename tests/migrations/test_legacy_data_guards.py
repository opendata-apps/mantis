"""Guards in the migrations that existing data could trip.

A row that violates a new CHECK
aborts ADD CONSTRAINT with "is violated by some row", which names no row, and
a dropped column takes whatever only it recorded along. Each migration names
the offending ids itself and stops before either happens.
"""

import pytest
import sqlalchemy as sa
from alembic.command import upgrade

from tests.test_config import MigrationsConfig

pytestmark = pytest.mark.usefixtures("app_ctx")


@pytest.fixture
def engine(clean_db):
    engine = sa.create_engine(MigrationsConfig.URI)
    yield engine
    engine.dispose()


def test_plz_out_of_range_names_the_row(engine, alembic_config):
    upgrade(alembic_config, "d7c2a9e41f05")
    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO beschreibung (id, beschreibung) VALUES (1, 'Im Garten')"
            )
        )
        row_id = conn.execute(
            sa.text("""
                INSERT INTO fundorte
                    (plz, ort, strasse, kreis, land, beschreibung,
                     longitude, latitude, ablage)
                VALUES
                    (123456, 'Drepkau', '', 'Spree-Neiße', 'Brandenburg', 1,
                     '14.1', '51.7', '2023/x.webp')
                RETURNING id
            """)
        ).scalar_one()

    with pytest.raises(Exception, match=r"outside 0\.\.99999") as excinfo:
        upgrade(alembic_config, "e3a1c5b7d209")

    assert f"{row_id} (123456)" in str(excinfo.value)


def test_unknown_status_names_the_report(engine, alembic_config):
    upgrade(alembic_config, "f4b8d2c6e017")
    with engine.begin() as conn:
        report_id = conn.execute(
            sa.text(
                "INSERT INTO meldungen (dat_fund_von, statuses) "
                "VALUES ('2025-06-01', '{OPEN,WAIT}') RETURNING id"
            )
        ).scalar_one()

    with pytest.raises(Exception, match="no legal status combination") as excinfo:
        upgrade(alembic_config, "a8c4e2f6b317")

    assert f"{report_id} ({{OPEN,WAIT}})" in str(excinfo.value)


def test_legacy_status_combinations_are_normalised(engine, alembic_config):
    upgrade(alembic_config, "f4b8d2c6e017")
    with engine.begin() as conn:
        conn.execute(
            sa.text("""
                INSERT INTO meldungen (id, dat_fund_von, statuses) VALUES
                    (1, '2025-06-01', '{APPR,UNKL}'),
                    (2, '2025-06-01', '{APPR,DEL}'),
                    (3, '2025-06-01', '{INFO}')
            """)
        )

    upgrade(alembic_config, "a8c4e2f6b317")

    with engine.connect() as conn:
        rows = conn.execute(
            sa.text("SELECT id, statuses FROM meldungen ORDER BY id")
        ).all()
    assert rows == [(1, ["APPR"]), (2, ["DEL"]), (3, ["OPEN", "INFO"])]


def test_unknown_user_role_names_the_user(engine, alembic_config):
    upgrade(alembic_config, "e8a2c6d4f371")
    with engine.begin() as conn:
        user_id = conn.execute(
            sa.text(
                "INSERT INTO users (user_id, user_name, user_rolle) "
                "VALUES ('legacy-user', 'Muster M.', '3') RETURNING id"
            )
        ).scalar_one()

    with pytest.raises(Exception, match="not a known role") as excinfo:
        upgrade(alembic_config, "f2c8e6a4b513")

    assert f"{user_id} ('3')" in str(excinfo.value)


def test_deletion_recorded_only_in_deleted_names_the_report(engine, alembic_config):
    upgrade(alembic_config, "a8c4e2f6b317")
    with engine.begin() as conn:
        report_id = conn.execute(
            sa.text(
                "INSERT INTO meldungen (dat_fund_von, statuses, deleted) "
                "VALUES ('2025-06-01', '{APPR}', true) RETURNING id"
            )
        ).scalar_one()

    with pytest.raises(Exception, match="deleted but not DEL") as excinfo:
        upgrade(alembic_config, "c9d5f1a3e825")

    assert f"{report_id} ({{APPR}})" in str(excinfo.value)
