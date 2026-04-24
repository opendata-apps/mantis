"""Tests for database population functions."""

import pytest
from unittest.mock import patch
from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError

from app.database.populate import (
    populate_beschreibung,
    populate_all,
)
from app.database.models import TblFundortBeschreibung


class TestPopulateFunctions:
    """Test suite for database population functions."""

    def test_populate_beschreibung_idempotent(self, session):
        """Test that populate_beschreibung doesn't duplicate existing data."""
        initial_count = session.scalar(
            select(func.count()).select_from(TblFundortBeschreibung)
        )
        assert initial_count > 0

        populate_beschreibung(session)

        final_count = session.scalar(
            select(func.count()).select_from(TblFundortBeschreibung)
        )
        assert final_count == initial_count

    def test_populate_beschreibung_database_error(self, session):
        """Test handling of database errors during population."""
        with patch.object(session, "get", side_effect=SQLAlchemyError("DB Error")):
            with pytest.raises(SQLAlchemyError):
                populate_beschreibung(session)

    @patch("app.database.vg5000_fill_aemter.import_aemter_data")
    @patch("app.database.populate.populate_beschreibung")
    def test_populate_all_success(self, mock_beschreibung, mock_aemter, session):
        """Test successful execution of populate_all."""
        mock_json_data = '{"test": "data"}'

        populate_all(session, mock_json_data)

        mock_beschreibung.assert_called_once_with(session)
        mock_aemter.assert_called_once_with(session, mock_json_data)

    @patch("app.database.vg5000_fill_aemter.import_aemter_data")
    def test_populate_all_beschreibung_error_stops_pipeline(self, mock_aemter, session):
        """Test populate_all when beschreibung population fails."""
        mock_json_data = '{"test": "data"}'

        with patch(
            "app.database.populate.populate_beschreibung",
            side_effect=Exception("Beschreibung failed"),
        ):
            with pytest.raises(Exception, match="Beschreibung failed"):
                populate_all(session, mock_json_data)

        mock_aemter.assert_not_called()

    @patch(
        "app.database.vg5000_fill_aemter.import_aemter_data",
        side_effect=Exception("Import failed"),
    )
    @patch("app.database.populate.populate_beschreibung")
    def test_populate_all_swallows_import_error(
        self, mock_beschreibung, mock_aemter, session
    ):
        """Test populate_all catches import errors without raising."""
        mock_json_data = '{"test": "data"}'

        populate_all(session, mock_json_data)

        mock_beschreibung.assert_called_once()
        mock_aemter.assert_called_once()

    @patch("app.database.vg5000_fill_aemter.import_aemter_data")
    @patch("app.database.populate.populate_beschreibung")
    def test_populate_all_skips_aemter_when_no_data(
        self, mock_beschreibung, mock_aemter, session
    ):
        """Test populate_all skips aemter when vg5000_json_data is None."""
        populate_all(session, None)

        mock_beschreibung.assert_called_once_with(session)
        mock_aemter.assert_not_called()
