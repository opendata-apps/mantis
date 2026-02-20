"""Tests for the Aemter (administrative areas) database table functionality."""

from sqlalchemy import select
from app.database.aemter_koordinaten import TblAemterCoordinaten


def test_aemter_json_properties_round_trip(session):
    """Test that JSON properties column stores and retrieves correctly."""
    properties = {"OBJID": "TEST123", "GEN": "Test Area", "BEZ": "Gemeinde"}

    new_area = TblAemterCoordinaten(ags=99999, gen="Test Area", properties=properties)
    session.add(new_area)
    session.flush()

    result = session.scalar(
        select(TblAemterCoordinaten).where(TblAemterCoordinaten.ags == 99999)
    )

    assert result is not None
    assert result.gen == "Test Area"
    assert result.properties["OBJID"] == "TEST123"
    assert result.properties == properties
