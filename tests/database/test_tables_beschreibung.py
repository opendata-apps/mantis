"""Tests for the Beschreibung (description) database table functionality."""

from sqlalchemy import select, func
from app.database.fundortbeschreibung import TblFundortBeschreibung


def test_table_beschreibung_record_count(session):
    """Test that the description table contains the expected number of records.

    This test verifies that the initial data load includes the correct
    number of location description categories.
    """
    # Use SQLAlchemy 2.0 select() pattern
    result = session.scalars(select(TblFundortBeschreibung)).all()

    # Verify the expected number of records
    assert len(result) == 12, "Expected 12 description categories in the test database"


def test_table_beschreibung_create_and_query(session):
    """Test creating and querying a new description record.

    This test verifies the ORM functionality for creating and
    retrieving description records.
    """
    # Find the maximum ID currently in the table to avoid duplicates
    max_id = session.scalar(select(func.max(TblFundortBeschreibung.id))) or 0
    test_id = max_id + 1

    # Create a new test description
    new_description = TblFundortBeschreibung(
        id=test_id, beschreibung="Test Description"
    )

    # Add and commit to the database
    session.add(new_description)
    session.commit()

    # Query the record back using SQLAlchemy 2.0 select() pattern
    result = session.scalar(
        select(TblFundortBeschreibung).where(TblFundortBeschreibung.id == test_id)
    )

    # Verify the record was created correctly
    assert result is not None, "Should find the new description record"
    assert result.beschreibung == "Test Description", "Description text should match"

    # Test to_dict method
    record_dict = result.to_dict()
    assert record_dict["id"] == test_id
    assert record_dict["beschreibung"] == "Test Description"
