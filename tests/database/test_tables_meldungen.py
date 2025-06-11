"""Tests for the Meldungen (Sightings) database table functionality."""
from app.database.fundmeldungen import TblMeldungen


def test_table_meldungen_record_count(session):
    """Test that the sightings table has the expected number of test records."""
    # Use ORM query instead of raw SQL
    result = session.query(TblMeldungen).all()
    assert len(result) == 20, "Expected 20 test records in the meldungen table"


def test_table_meldungen_query_capabilities(session):
    """Test various query capabilities on the sightings table."""
    # Get total count first to understand the data
    total_count = session.query(TblMeldungen).count()
    assert total_count == 20, "Expected 20 test records in total"

    # Check records with non-null deletion status
    deleted_records = session.query(TblMeldungen).filter(
        TblMeldungen.deleted.is_(True)
    ).all()

    non_deleted_records = session.query(TblMeldungen).filter(
        TblMeldungen.deleted.is_(False)
    ).all()

    # Check records with null deletion status
    null_deletion_status = session.query(TblMeldungen).filter(
        TblMeldungen.deleted.is_(None)
    ).count()

    # Diagnostic info: deleted + non-deleted + null status should equal total count

    # Ensure we can account for all records (deleted + non-deleted + null status)
    assert len(deleted_records) + len(non_deleted_records) + null_deletion_status == total_count
