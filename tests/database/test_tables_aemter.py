"""Tests for the Aemter (administrative areas) database table functionality."""

from sqlalchemy import select
from app.database.aemter_koordinaten import TblAemterCoordinaten


def test_table_aemter_structure(session):
    """Test that the administrative areas table has the expected structure.

    This test verifies that the table structure works as expected by inserting
    and retrieving a test record with ORM.
    """
    # Insert test data
    test_properties = {
        "OBJID": "TEST001",
        "GEN": "Test Town",
        "BEZ": "Gemeinde",
        "ARS": "12345",
    }

    # Create a test record
    test_area = TblAemterCoordinaten(
        ags=12345, gen="Test Town", properties=test_properties
    )

    # Add and commit to the database
    session.add(test_area)
    session.commit()

    # Query the data back using SQLAlchemy 2.0 select() pattern
    result = session.scalar(
        select(TblAemterCoordinaten).where(TblAemterCoordinaten.ags == 12345)
    )

    # Verify the record was inserted correctly
    assert result is not None, "Test record should exist"
    assert result.gen == "Test Town", "Name should match"
    assert result.properties == test_properties, "Properties should match"


def test_table_aemter_manual_insert(session):
    """Test manually inserting a record into the administrative areas table."""
    # Create a test record
    properties = {"OBJID": "TEST123", "GEN": "Test Area", "BEZ": "Gemeinde"}

    # Insert a new record
    new_area = TblAemterCoordinaten(ags=99999, gen="Test Area", properties=properties)

    session.add(new_area)
    session.commit()

    # Verify it was inserted correctly using SQLAlchemy 2.0 select() pattern
    test_area = session.scalar(
        select(TblAemterCoordinaten).where(TblAemterCoordinaten.ags == 99999)
    )

    assert test_area is not None
    assert test_area.gen == "Test Area"
    assert test_area.properties["OBJID"] == "TEST123"
