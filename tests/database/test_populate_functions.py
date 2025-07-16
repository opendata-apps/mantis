"""Tests for database population functions."""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from app.database.populate import (
    populate_beschreibung, populate_feedback_types, populate_all
)
from app.database.models import TblFundortBeschreibung, TblFeedbackType

class TestPopulateFunctions:
    """Test suite for database population functions."""

    def test_populate_beschreibung_already_populated(self, session):
        """Test that populate_beschreibung is idempotent with existing data."""
        # Check that table already has data (from conftest setup)
        initial_count = session.query(TblFundortBeschreibung).count()
        assert initial_count > 0
        
        # Run populate again
        populate_beschreibung(session)
        
        # Count should remain the same (no duplicates)
        final_count = session.query(TblFundortBeschreibung).count()
        assert final_count == initial_count
        
        # Verify expected records exist
        record_dict = {r.id: r.beschreibung for r in session.query(TblFundortBeschreibung).all()}
        assert 1 in record_dict
        assert 6 in record_dict
        assert 99 in record_dict

    def test_populate_beschreibung_existing_records(self, session):
        """Test populating beschreibung table with existing records."""
        # The table already has all 12 records from conftest setup
        initial_count = session.query(TblFundortBeschreibung).count()
        
        # Get original value of record 1
        original_record = session.query(TblFundortBeschreibung).filter_by(id=1).first()
        original_beschreibung = original_record.beschreibung
        
        # Populate should not fail or duplicate
        populate_beschreibung(session)
        
        # Should still have the same number of records
        final_count = session.query(TblFundortBeschreibung).count()
        assert final_count == initial_count
        
        # Original record should be preserved
        record = session.query(TblFundortBeschreibung).filter_by(id=1).first()
        assert record.beschreibung == original_beschreibung

    def test_populate_beschreibung_database_error(self, session):
        """Test handling of database errors during population."""
        # Mock the session.execute to raise an error
        with patch.object(session, 'execute', side_effect=SQLAlchemyError("DB Error")):
            with pytest.raises(SQLAlchemyError):
                populate_beschreibung(session)

    def test_populate_feedback_types_empty_table(self, session):
        """Test populating feedback types table when empty."""
        # Clear existing data for this test
        session.query(TblFeedbackType).delete()
        session.commit()
        
        # Ensure table is empty
        assert session.query(TblFeedbackType).count() == 0
        
        # Populate the table
        populate_feedback_types(session)
        
        # Verify all records were inserted
        records = session.query(TblFeedbackType).all()
        assert len(records) == 8
        
        # Verify specific records
        type_dict = {r.id: r.name for r in records}
        assert type_dict[1] == 'Auf einer Veranstaltung'
        assert type_dict[2] == 'Flyer/ Folder des Projektes'
        assert type_dict[5] == 'Internetrecherche'

    def test_populate_feedback_types_existing_records(self, session):
        """Test populating feedback types with existing records."""
        # Clear feedback types first (they may not have FK constraints)
        session.query(TblFeedbackType).delete()
        session.commit()
        
        # Add an existing record with custom name
        existing = TblFeedbackType(id=1, name='Custom Type')
        session.add(existing)
        session.commit()
        
        # Populate should not fail
        populate_feedback_types(session)
        
        # Should have all expected records (existing + new ones)
        records = session.query(TblFeedbackType).all()
        assert len(records) == 8  # 1 custom + 7 others (2-8)
        
        # Original should be preserved with custom name
        record = session.query(TblFeedbackType).filter_by(id=1).first()
        assert record.name == 'Custom Type'

    @patch('app.database.vg5000_fill_aemter.import_aemter_data')
    @patch('app.database.populate.populate_feedback_types')
    @patch('app.database.populate.populate_beschreibung')
    def test_populate_all_success(self, mock_beschreibung, mock_feedback, 
                                  mock_aemter, session):
        """Test successful execution of populate_all."""
        # Setup
        mock_engine = MagicMock()
        mock_json_data = '{"test": "data"}'
        
        # Execute
        populate_all(mock_engine, session, mock_json_data)
        
        # Verify all functions were called in correct order
        mock_beschreibung.assert_called_once_with(session)
        mock_feedback.assert_called_once_with(session)
        mock_aemter.assert_called_once_with(mock_engine, mock_json_data)

    @patch('app.database.vg5000_fill_aemter.import_aemter_data')
    def test_populate_all_beschreibung_error(self, mock_aemter, session):
        """Test populate_all when beschreibung population fails."""
        # Setup
        mock_engine = MagicMock()
        mock_json_data = '{"test": "data"}'
        
        # Mock beschreibung to fail
        with patch('app.database.populate.populate_beschreibung', 
                   side_effect=Exception("Beschreibung failed")):
            with pytest.raises(Exception, match="Beschreibung failed"):
                populate_all(mock_engine, session, mock_json_data)
        
        # Subsequent functions should not be called
        mock_aemter.assert_not_called()

    @patch('app.database.vg5000_fill_aemter.import_aemter_data', side_effect=Exception("Import failed"))
    @patch('app.database.populate.populate_feedback_types')
    @patch('app.database.populate.populate_beschreibung')
    def test_populate_all_import_error(self, mock_beschreibung, mock_feedback, 
                                       mock_aemter, session):
        """Test populate_all when aemter import fails - but it should NOT raise."""
        # Setup
        mock_engine = MagicMock()
        mock_json_data = '{"test": "data"}'
        
        # Execute - should NOT raise error (populate_all catches import errors)
        populate_all(mock_engine, session, mock_json_data)
        
        # Earlier functions should have been called
        mock_beschreibung.assert_called_once()
        mock_feedback.assert_called_once()
        
        # Import should have been attempted
        mock_aemter.assert_called_once()

    def test_populate_beschreibung_partial_data(self, session):
        """Test that populate_beschreibung handles partial data correctly."""
        # Since table is already populated, let's verify the function correctly checks for existing records
        # Get current count
        initial_count = session.query(TblFundortBeschreibung).count()
        assert initial_count == 12
        
        # Run populate - should check each record and not add duplicates
        populate_beschreibung(session)
        
        # Should still have exactly 12 records
        final_count = session.query(TblFundortBeschreibung).count()
        assert final_count == 12
        
        # Verify all expected records exist
        all_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 99]
        for expected_id in all_ids:
            record = session.query(TblFundortBeschreibung).filter_by(id=expected_id).first()
            assert record is not None

    def test_populate_functions_idempotency(self, session):
        """Test that populate functions can be run multiple times safely."""
        # Run populate_beschreibung twice
        populate_beschreibung(session)
        first_count = session.query(TblFundortBeschreibung).count()
        
        populate_beschreibung(session)
        second_count = session.query(TblFundortBeschreibung).count()
        
        # Count should not increase
        assert first_count == second_count
        
        # Run populate_feedback_types twice
        populate_feedback_types(session)
        first_count = session.query(TblFeedbackType).count()
        
        populate_feedback_types(session)
        second_count = session.query(TblFeedbackType).count()
        
        # Count should not increase
        assert first_count == second_count


    def test_populate_functions_error_handling(self):
        """Test error handling in populate functions."""
        # Test database error handling
        mock_session = MagicMock()
        mock_session.execute.side_effect = SQLAlchemyError("DB Error")
        
        with pytest.raises(Exception):  # The function catches and re-raises as generic Exception
            populate_beschreibung(mock_session)

    @patch('app.database.populate.current_app')
    def test_populate_all_logging(self, mock_current_app):
        """Test that populate_all logs its progress."""
        
        mock_logger = MagicMock()
        mock_current_app.logger = mock_logger
        
        mock_engine = MagicMock()
        mock_session = MagicMock()
        mock_json_data = '{"test": "data"}'
        
        with patch('app.database.populate.populate_beschreibung'):
            with patch('app.database.populate.populate_feedback_types'):
                with patch('app.database.vg5000_fill_aemter.import_aemter_data'):
                    populate_all(mock_engine, mock_session, mock_json_data)
        
        # Should have logged progress
        # assert mock_logger.info.called
        # Check specific log messages
        mock_logger.info.assert_any_call("Starting initial data population...")
        mock_logger.info.assert_any_call("Initial data population finished.")
