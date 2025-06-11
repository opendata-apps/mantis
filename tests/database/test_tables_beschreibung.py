"""Tests for the Beschreibung (description) database table functionality."""
from app.database.fundortbeschreibung import TblFundortBeschreibung
import sqlalchemy as sa


def test_table_beschreibung_record_count(session):
    """Test that the description table contains the expected number of records.
    
    This test verifies that the initial data load includes the correct
    number of location description categories.
    """
    # Use ORM query instead of raw SQL
    result = session.query(TblFundortBeschreibung).all()

    # Verify the expected number of records
    assert len(result) == 12, "Expected 12 description categories in the test database"


def test_table_beschreibung_create_and_query(session):
    """Test creating and querying a new description record.
    
    This test verifies the ORM functionality for creating and
    retrieving description records.
    """
    # Find the maximum ID currently in the table to avoid duplicates
    max_id = session.query(sa.func.max(TblFundortBeschreibung.id)).scalar() or 0
    test_id = max_id + 1

    # Create a new test description
    new_description = TblFundortBeschreibung(
        id=test_id,
        beschreibung="Test Description"
    )

    # Add and commit to the database
    session.add(new_description)
    session.commit()

    # Query the record back using ORM
    result = session.query(TblFundortBeschreibung).filter(
        TblFundortBeschreibung.id == test_id
    ).first()

    # Verify the record was created correctly
    assert result is not None, "Should find the new description record"
    assert result.beschreibung == "Test Description", "Description text should match"

    # Test to_dict method
    record_dict = result.to_dict()
    assert record_dict["id"] == test_id
    assert record_dict["beschreibung"] == "Test Description"
