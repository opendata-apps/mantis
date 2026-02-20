"""Tests for the Beschreibung (description) database table functionality."""

from sqlalchemy import select, func
from app.database.fundortbeschreibung import TblFundortBeschreibung


def test_beschreibung_to_dict(session):
    """Test that to_dict() serialization returns correct fields."""
    max_id = session.scalar(select(func.max(TblFundortBeschreibung.id))) or 0
    test_id = max_id + 1

    new_description = TblFundortBeschreibung(
        id=test_id, beschreibung="Test Description"
    )
    session.add(new_description)
    session.flush()

    result = session.scalar(
        select(TblFundortBeschreibung).where(TblFundortBeschreibung.id == test_id)
    )

    assert result is not None
    record_dict = result.to_dict()
    assert record_dict["id"] == test_id
    assert record_dict["beschreibung"] == "Test Description"
