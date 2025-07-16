"""Test image date synchronization functionality"""
import tempfile
from datetime import datetime, date
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
from app.database.fundmeldungen import TblMeldungen
from app.database.fundorte import TblFundorte
from app.routes.admin import update_report_image_date


@pytest.fixture
def mock_fundorte_with_image(session):
    """Create a fundorte record with an image path"""
    fundorte = TblFundorte(
        id=99999,
        plz='12345',
        ort='TestCity',
        strasse='Test Street',
        kreis='Test District',
        land='Brandenburg',
        amt='Test Amt',
        mtb='1234',
        beschreibung=1,  # Using existing beschreibung ID from test data
        latitude='52.5',
        longitude='13.4',
        ablage='2024/2024-07-15/TestCity-20240715120000-testuser123.webp'
    )
    session.add(fundorte)
    session.commit()
    return fundorte


@pytest.fixture
def mock_meldung_with_image(session, mock_fundorte_with_image):
    """Create a meldung record linked to fundorte with image"""
    meldung = TblMeldungen(
        id=99999,
        dat_fund_von=date(2024, 7, 15),
        dat_meld=datetime.now(),
        fo_zuordnung=mock_fundorte_with_image.id,
        tiere=1,
        art_m=1,
        art_w=0,
        art_n=0,
        art_o=0,
        art_f=0,
        fo_quelle="T",
        deleted=False
    )
    session.add(meldung)
    session.commit()
    return meldung


def test_update_report_image_date_success(app, session, mock_meldung_with_image, mock_fundorte_with_image):
    """Test successful image move when date changes"""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('app.routes.admin.current_app') as mock_app:
            # Mock the app config
            mock_app.config = {'UPLOAD_FOLDER': temp_dir}
            mock_app.logger = MagicMock()
            
            # Create the original file structure
            original_dir = Path(temp_dir) / '2024' / '2024-07-15'
            original_dir.mkdir(parents=True, exist_ok=True)
            original_file = original_dir / 'TestCity-20240715120000-testuser123.webp'
            original_file.write_text('test image content')
            
            # Update to new date
            new_date = date(2024, 8, 20)
            result, status_code = update_report_image_date(mock_meldung_with_image.id, new_date)
            
            # Verify success
            assert status_code == 200
            assert result['status'] == 'success'
            
            # Check file was moved
            new_file_path = Path(temp_dir) / '2024' / '2024-08-20' / 'TestCity-20240820000000-testuser123.webp'
            assert new_file_path.exists()
            assert new_file_path.read_text() == 'test image content'
            
            # Check old file removed
            assert not original_file.exists()
            
            # Check database updated
            session.refresh(mock_fundorte_with_image)
            assert mock_fundorte_with_image.ablage == '2024/2024-08-20/TestCity-20240820000000-testuser123.webp'


def test_update_report_image_date_no_image(app, session):
    """Test handling when there's no image to move"""
    # Create fundorte without image
    fundorte = TblFundorte(
        id=99998,
        plz='12345',
        ort='TestCity',
        strasse='Test Street',
        kreis='Test District',
        land='Brandenburg',
        amt='Test Amt',
        mtb='1234',
        beschreibung=1,  # Using existing beschreibung ID from test data
        latitude='52.5',
        longitude='13.4',
        ablage=''  # Empty string instead of None
    )
    session.add(fundorte)
    session.commit()  # Commit fundorte first
    
    meldung = TblMeldungen(
        id=99998,
        dat_fund_von=date(2024, 7, 15),
        dat_meld=datetime.now(),
        fo_zuordnung=fundorte.id,
        tiere=1,
        art_m=1,
        art_w=0,
        art_n=0,
        art_o=0,
        art_f=0,
        fo_quelle="T",
        deleted=False
    )
    session.add(meldung)
    session.commit()
    
    with patch('app.routes.admin.current_app') as mock_app:
        mock_app.config = {'UPLOAD_FOLDER': '/tmp'}
        
        result, status_code = update_report_image_date(meldung.id, date(2024, 8, 20))
        
        assert status_code == 200
        assert result['status'] == 'no_image'


def test_update_report_image_date_file_not_found(app, session):
    """Test handling when image file doesn't exist"""
    # Create test data with different IDs
    fundorte = TblFundorte(
        id=99997,
        plz='12345',
        ort='TestCity',
        strasse='Test Street',
        kreis='Test District',
        land='Brandenburg',
        amt='Test Amt',
        mtb='1234',
        beschreibung=1,
        latitude='52.5',
        longitude='13.4',
        ablage='2024/2024-07-15/TestCity-20240715120000-testuser123.webp'
    )
    session.add(fundorte)
    session.commit()
    
    meldung = TblMeldungen(
        id=99997,
        dat_fund_von=date(2024, 7, 15),
        dat_meld=datetime.now(),
        fo_zuordnung=fundorte.id,
        tiere=1,
        art_m=1,
        art_w=0,
        art_n=0,
        art_o=0,
        art_f=0,
        fo_quelle="T",
        deleted=False
    )
    session.add(meldung)
    session.commit()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('app.routes.admin.current_app') as mock_app:
            mock_app.config = {'UPLOAD_FOLDER': temp_dir}
            
            # Don't create the file, just try to update
            result, status_code = update_report_image_date(meldung.id, date(2024, 8, 20))
            
            assert status_code == 404
            assert 'Image file not found' in result['error']


def test_update_report_image_date_same_date(app, session):
    """Test when source and destination are the same"""
    # Create test data with different IDs
    fundorte = TblFundorte(
        id=99996,
        plz='12345',
        ort='TestCity',
        strasse='Test Street',
        kreis='Test District',
        land='Brandenburg',
        amt='Test Amt',
        mtb='1234',
        beschreibung=1,
        latitude='52.5',
        longitude='13.4',
        ablage='2024/2024-07-15/TestCity-20240715120000-testuser123.webp'
    )
    session.add(fundorte)
    session.commit()
    
    meldung = TblMeldungen(
        id=99996,
        dat_fund_von=date(2024, 7, 15),
        dat_meld=datetime.now(),
        fo_zuordnung=fundorte.id,
        tiere=1,
        art_m=1,
        art_w=0,
        art_n=0,
        art_o=0,
        art_f=0,
        fo_quelle="T",
        deleted=False
    )
    session.add(meldung)
    session.commit()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch('app.routes.admin.current_app') as mock_app:
            mock_app.config = {'UPLOAD_FOLDER': temp_dir}
            
            # Create the file
            original_dir = Path(temp_dir) / '2024' / '2024-07-15'
            original_dir.mkdir(parents=True, exist_ok=True)
            original_file = original_dir / 'TestCity-20240715120000-testuser123.webp'
            original_file.write_text('test image content')
            
            # Update to same date
            result, status_code = update_report_image_date(meldung.id, date(2024, 7, 15))
            
            assert status_code == 200
            # The file gets moved with a new timestamp even for the same date
            assert result['status'] == 'success'
            
            # Check that file still exists in same date folder
            files_in_dir = list(original_dir.glob('*.webp'))
            assert len(files_in_dir) == 1
            assert files_in_dir[0].name.startswith('TestCity-')
            assert files_in_dir[0].name.endswith('-testuser123.webp')


def test_update_report_record_not_found(app, session):
    """Test handling when report doesn't exist"""
    with patch('app.routes.admin.current_app') as mock_app:
        mock_app.config = {'UPLOAD_FOLDER': '/tmp'}
        
        result, status_code = update_report_image_date(99995, date(2024, 8, 20))
        
        assert status_code == 404
        assert result['error'] == 'Report not found'