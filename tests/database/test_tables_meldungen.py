"""Tests for the Meldungen (Sightings) database table functionality."""

from sqlalchemy import select, func
from app.database.fundmeldungen import TblMeldungen


def test_table_meldungen_record_count(session):
    """Test that the sightings table has the expected number of test records."""
    # Use SQLAlchemy 2.0 select() pattern
    result = session.scalars(select(TblMeldungen)).all()
    assert len(result) == 20, "Expected 20 test records in the meldungen table"


def test_table_meldungen_query_capabilities(session):
    """Test various query capabilities on the sightings table."""
    # Get total count first to understand the data
    total_count = session.scalar(select(func.count()).select_from(TblMeldungen))
    assert total_count == 20, "Expected 20 test records in total"

    # Check records with non-null deletion status
    deleted_records = session.scalars(
        select(TblMeldungen).where(TblMeldungen.deleted.is_(True))
    ).all()

    non_deleted_records = session.scalars(
        select(TblMeldungen).where(TblMeldungen.deleted.is_(False))
    ).all()

    # Check records with null deletion status
    null_deletion_status = session.scalar(
        select(func.count()).select_from(TblMeldungen).where(TblMeldungen.deleted.is_(None))
    )

    # Diagnostic info: deleted + non-deleted + null status should equal total count

    # Ensure we can account for all records (deleted + non-deleted + null status)
    assert (
        len(deleted_records) + len(non_deleted_records) + null_deletion_status
        == total_count
    )
