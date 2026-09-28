"""Guards in the coordinate migration (f4b8d2c6e017).

Production carries two 2023 fundorte whose latitude and longitude are the
literal string '???'. Casting those aborts the migration with a
bare "invalid input syntax", which names neither the column nor the row — so
each guard has to report the offending ids instead.
"""

import pytest
import sqlalchemy as sa
from alembic.command import upgrade

from tests.test_config import MigrationsConfig

BEFORE = "e3a1c5b7d209"
COORDINATES = "f4b8d2c6e017"

pytestmark = pytest.mark.usefixtures("app_ctx")


@pytest.fixture
def at_previous_revision(alembic_config, clean_db):
    """Schema one revision before coordinates become double precision."""
    upgrade(alembic_config, BEFORE)
    engine = sa.create_engine(MigrationsConfig.URI)
    yield engine
    engine.dispose()


def _insert_fundort(engine, *, latitude, longitude):
    with engine.connect() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO beschreibung (id, beschreibung) VALUES (1, 'Im Garten')"
                " ON CONFLICT (id) DO NOTHING"
            )
        )
        row_id = conn.execute(
            sa.text("""
                INSERT INTO fundorte
                    (plz, ort, strasse, kreis, land, beschreibung,
                     longitude, latitude, ablage)
                VALUES
                    ('03116', 'Drepkau', '', 'Spree-Neiße', 'Brandenburg', 1,
                     :lon, :lat, '2023/x.webp')
                RETURNING id
            """),
            {"lat": latitude, "lon": longitude},
        ).scalar_one()
        conn.commit()
    return row_id


def test_unparseable_coordinate_names_the_row(at_previous_revision, alembic_config):
    row_id = _insert_fundort(at_previous_revision, latitude="???", longitude="???")

    with pytest.raises(Exception, match="not numeric") as excinfo:
        upgrade(alembic_config, COORDINATES)

    message = str(excinfo.value)
    assert str(row_id) in message, (
        "The guard must name the offending row so it can be repaired."
    )


def test_out_of_range_coordinate_names_the_row(at_previous_revision, alembic_config):
    row_id = _insert_fundort(at_previous_revision, latitude="91.5", longitude="13.0")

    with pytest.raises(Exception, match="out of geographic range") as excinfo:
        upgrade(alembic_config, COORDINATES)

    assert str(row_id) in str(excinfo.value)


def test_comma_decimal_separator_still_migrates(at_previous_revision, alembic_config):
    """65 rows from 2023 store '51,430356'; the USING clause has to keep them."""
    row_id = _insert_fundort(
        at_previous_revision, latitude="51,430356", longitude="13,06211"
    )

    upgrade(alembic_config, COORDINATES)

    with at_previous_revision.connect() as conn:
        latitude = conn.execute(
            sa.text("SELECT latitude FROM fundorte WHERE id = :id"), {"id": row_id}
        ).scalar_one()
    assert latitude == pytest.approx(51.430356)
