"""Tests for database population functions."""

from unittest.mock import patch

import pytest
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.database.models import TblFundortBeschreibung
from app.database.populate import (
    populate_all,
    populate_beschreibung,
)


@pytest.mark.usefixtures("app_ctx")
class TestPopulateFunctions:
    """Test suite for database population functions."""

    def test_populate_beschreibung_idempotent(self, session):
        """Test that populate_beschreibung doesn't duplicate existing data."""
        descriptions = select(
            TblFundortBeschreibung.id, TblFundortBeschreibung.beschreibung
        )
        before = dict(session.execute(descriptions).all())
        assert before[1] == "Im Haus"
        assert before[99] == "Anderer Fundort"
        populate_beschreibung(session)
        assert dict(session.execute(descriptions).all()) == before

    def test_populate_beschreibung_database_error(self, session):
        """Test handling of database errors during population."""
        with (
            patch.object(session, "get", side_effect=SQLAlchemyError("DB Error")),
            pytest.raises(SQLAlchemyError),
        ):
            populate_beschreibung(session)

    @patch("app.database.vg5000_fill_aemter.import_aemter_data")
    def test_populate_all_beschreibung_error_stops_pipeline(self, mock_aemter, session):
        """Test populate_all when beschreibung population fails."""
        mock_json_data = '{"test": "data"}'

        with (
            patch(
                "app.database.populate.populate_beschreibung",
                side_effect=Exception("Beschreibung failed"),
            ),
            pytest.raises(Exception, match="Beschreibung failed"),
        ):
            populate_all(session, mock_json_data)

        mock_aemter.assert_not_called()
