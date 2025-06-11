"""Tests for admin routes including reviewer interface and data management."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
import json

from app.database.models import (
    TblMeldungen, TblFundorte, TblUsers, TblMeldungUser,
    TblFundortBeschreibung
)


class TestAdminRoutes:
    """Test suite for admin and reviewer routes."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, session):
        """Set up test data for admin tests."""
        self.session = session
        
        # Create test user with reviewer role
        self.reviewer_user = TblUsers(
            user_id='9999',
            user_name='Test Reviewer',
            user_kontakt='reviewer@test.com',
            user_rolle='9'
        )
        session.add(self.reviewer_user)
        
        # Create regular user (non-reviewer)
        self.regular_user = TblUsers(
            user_id='1111',
            user_name='Regular User',
            user_kontakt='user@test.com',
            user_rolle='1'
        )
        session.add(self.regular_user)
        
        # Use an existing description from the pre-populated data
        self.test_description = session.query(TblFundortBeschreibung).filter_by(id=1).first()
        if not self.test_description:
            # Fallback if somehow the initial data isn't there
            self.test_description = session.query(TblFundortBeschreibung).first()
        
        assert self.test_description, "No beschreibung records found in database"
        
        # Create test location
        self.test_location = TblFundorte(
            mtb='3644',
            longitude='13.404954',
            latitude='52.520008',
            ort='Test City',
            land='Test State',
            kreis='Test District',
            strasse='Test Street',
            plz=10178,
            amt='Test Amt',
            ablage='test_image.jpg',
            beschreibung=self.test_description.id
        )
        session.add(self.test_location)
        session.flush()
        
        # Create test sighting
        self.test_sighting = TblMeldungen(
            dat_fund_von=datetime.now().date() - timedelta(days=7),
            dat_meld=datetime.now().date(),
            fo_zuordnung=self.test_location.id,
            art_m=1,
            art_w=0,
            art_n=0,
            art_o=0,
            anm_melder='Test sighting',
            deleted=False,
            bearb_id=None,  # Not approved yet
            dat_bear=None
        )
        session.add(self.test_sighting)
        session.flush()
        
        # Create user-sighting relation
        self.test_relation = TblMeldungUser(
            id_meldung=self.test_sighting.id,
            id_user=self.reviewer_user.id
        )
        session.add(self.test_relation)
        
        session.commit()
        
        yield
        
        # Cleanup happens automatically with session rollback

    def test_reviewer_page_access_with_valid_reviewer(self, client):
        """Test that reviewers can access the reviewer page."""
        # Follow redirects to handle the automatic redirect to add default params
        response = client.get('/reviewer/9999', follow_redirects=True)
        assert response.status_code == 200
        # Check for admin panel content
        assert b'Admin Panel' in response.data or b'admin' in response.data.lower()
        # Check that session was set
        with client.session_transaction() as sess:
            assert sess.get('user_id') == '9999'

    def test_reviewer_page_access_with_invalid_user(self, client):
        """Test that non-reviewers cannot access the reviewer page."""
        # Non-existent user
        response = client.get('/reviewer/invalid')
        assert response.status_code == 403
        
        # Regular user (not reviewer)
        response = client.get('/reviewer/1111')
        assert response.status_code == 403

    def test_reviewer_page_filters(self, client):
        """Test filtering functionality on reviewer page."""
        # Test status filter
        response = client.get('/reviewer/9999?statusInput=offen&sort_order=id_desc')
        assert response.status_code == 200
        
        # Test with search query - need to include required params
        response = client.get('/reviewer/9999?q=Test&search_type=full_text&statusInput=offen&sort_order=id_desc')
        assert response.status_code == 200
        
        # Test date filters - need to include required params
        response = client.get('/reviewer/9999?dateFrom=2024-01-01&dateTo=2024-12-31&statusInput=offen&sort_order=id_desc')
        assert response.status_code == 200

    def test_reviewer_page_session_storage(self, client):
        """Test that user_id is stored in session when accessing reviewer page."""
        with client.session_transaction() as sess:
            assert 'user_id' not in sess
        
        # Follow redirects
        response = client.get('/reviewer/9999', follow_redirects=True)
        assert response.status_code == 200
        
        with client.session_transaction() as sess:
            assert sess['user_id'] == '9999'

    @patch('app.database.full_text_search.refresh_materialized_view')
    def test_reviewer_page_materialized_view_refresh(self, mock_refresh, client):
        """Test that materialized view is refreshed when needed."""
        # First access should trigger refresh - follow redirects
        response = client.get('/reviewer/9999', follow_redirects=True)
        assert response.status_code == 200
        mock_refresh.assert_called_once()

    def test_change_mantis_metadata_authenticated(self, client, session):
        """Test changing mantis metadata with authentication."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = '9999'
        
        # Test changing location data - ort (city)
        response = client.post(
            f'/change_mantis_meta_data/{self.test_sighting.id}',
            data={
                'type': 'ort',
                'new_data': 'Updated City'
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Verify the change in database
        location = session.get(TblFundorte, self.test_location.id)
        assert location.ort == 'Updated City'

    def test_change_mantis_metadata_unauthenticated(self, client):
        """Test that unauthenticated users cannot change metadata."""
        response = client.post(
            f'/change_mantis_meta_data/{self.test_sighting.id}',
            data={'beschreibung': '2'}
        )
        assert response.status_code == 403

    def test_toggle_approve_sighting(self, client, session):
        """Test approving/unapproving sightings."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = '9999'
        
        # Initial state should be unapproved
        assert self.test_sighting.bearb_id is None
        assert self.test_sighting.dat_bear is None
        
        # Toggle to approve
        response = client.post(f'/toggle_approve_sighting/{self.test_sighting.id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Verify in database
        session.refresh(self.test_sighting)
        assert self.test_sighting.bearb_id == '9999'
        assert self.test_sighting.dat_bear is not None

    def test_toggle_approve_sighting_without_email(self, client, session):
        """Test that approving works even when email sending is disabled."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = '9999'
        
        # Approve sighting (emails are disabled in test config)
        response = client.post(f'/toggle_approve_sighting/{self.test_sighting.id}')
        assert response.status_code == 200
        
        # Verify approval happened
        session.refresh(self.test_sighting)
        assert self.test_sighting.bearb_id == '9999'
        assert self.test_sighting.dat_bear is not None

    def test_delete_sighting(self, client, session):
        """Test soft deleting a sighting."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = '9999'
        
        # Delete sighting
        response = client.post(f'/delete_sighting/{self.test_sighting.id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Report successfully deleted'
        
        # Verify soft delete in database
        session.refresh(self.test_sighting)
        assert self.test_sighting.deleted is True

    def test_undelete_sighting(self, client, session):
        """Test undeleting a soft-deleted sighting."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = '9999'
        
        # First delete the sighting
        self.test_sighting.deleted = True
        session.commit()
        
        # Undelete sighting
        response = client.post(f'/undelete_sighting/{self.test_sighting.id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Report successfully undeleted'
        
        # Verify undelete in database
        session.refresh(self.test_sighting)
        assert self.test_sighting.deleted is False

    def test_change_mantis_gender(self, client, session):
        """Test changing mantis gender fields."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = '9999'
        
        # Change gender to female
        response = client.post(
            f'/change_mantis_gender/{self.test_sighting.id}',
            data={'new_gender': 'W'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Verify in database
        session.refresh(self.test_sighting)
        assert self.test_sighting.art_m == 0
        assert self.test_sighting.art_w == 1
        assert self.test_sighting.art_n == 0
        assert self.test_sighting.art_o == 0

    def test_change_mantis_count(self, client, session):
        """Test changing mantis count fields."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = '9999'
        
        # Update male count
        response = client.post(
            f'/change_mantis_count/{self.test_sighting.id}',
            data={
                'type': 'Männchen',
                'new_count': '2'
            }
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Verify in database
        session.refresh(self.test_sighting)
        assert self.test_sighting.art_m == 2

    def test_get_sighting_details(self, client):
        """Test getting sighting details."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = '9999'
        
        response = client.get(f'/get_sighting/{self.test_sighting.id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check that all expected fields are present
        assert 'id' in data
        assert 'dat_fund_von' in data
        assert 'ort' in data
        assert 'user_name' in data

    def test_export_xlsx_all_data(self, client):
        """Test exporting all data as Excel file."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = '9999'
        
        response = client.get('/admin/export/xlsx/all')
        assert response.status_code == 200
        assert response.content_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        # Verify we got data (Excel files start with PK for zip format)
        assert len(response.data) > 0
        assert response.data[:2] == b'PK'  # Excel files are zip archives

    def test_export_xlsx_approved_only(self, client, session):
        """Test exporting only approved data."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = '9999'
        
        # Approve the sighting
        self.test_sighting.bearb_id = '9999'
        self.test_sighting.dat_bear = datetime.now().date()
        session.commit()
        
        response = client.get('/admin/export/xlsx/accepted')
        assert response.status_code == 200
        assert response.content_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        # Verify we got data
        assert len(response.data) > 0
        assert response.data[:2] == b'PK'

    def test_alldata_view_access(self, client):
        """Test accessing the alldata view."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = '9999'
        
        response = client.get('/alldata')
        assert response.status_code == 200
        assert b'database' in response.data.lower()

    def test_get_table_data_api(self, client):
        """Test getting table data via API."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = '9999'
        
        # Test getting all_data_view table data
        response = client.get('/admin/get_table_data/all_data_view?page=1&per_page=10')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'data' in data
        assert 'total_items' in data
        assert 'columns' in data
        assert len(data['data']) > 0  # Should have at least our test sighting

    @pytest.mark.skip(reason="Requires materialized view to be populated with test data")
    def test_update_cell_valid_table(self, client, session):
        """Test updating a cell in a valid table."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = '9999'
        
        # Update anm_melder field
        response = client.post(
            '/admin/update_cell',
            json={
                'table': 'all_data_view',
                'meldungen_id': self.test_sighting.id,
                'column': 'anm_melder',
                'value': 'Updated comment'
            }
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Verify in database
        session.refresh(self.test_sighting)
        assert self.test_sighting.anm_melder == 'Updated comment'

    @pytest.mark.skip(reason="Requires materialized view to be populated with test data")
    def test_update_cell_non_editable_field(self, client):
        """Test that non-editable fields cannot be updated."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = '9999'
        
        # Try to update non-editable field (meldungen_id)
        response = client.post(
            '/admin/update_cell',
            json={
                'table': 'all_data_view',
                'meldungen_id': self.test_sighting.id,
                'column': 'meldungen_id',
                'value': '999'
            }
        )
        assert response.status_code == 403
        data = json.loads(response.data)
        assert 'not editable' in data['error']

    def test_static_file_serving(self, client):
        """Test serving static files through admin route."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = '9999'
        
        # Test accessing a file (assuming test file exists)
        response = client.get('/test_image.jpg')
        # Should either return the file or 404 if it doesn't exist
        assert response.status_code in [200, 404]


    def test_pagination_on_reviewer_page(self, client, session):
        """Test pagination functionality on reviewer page."""
        # Create multiple sightings for pagination
        for i in range(25):
            location = TblFundorte(
                mtb='3644',
                longitude='13.404954',
                latitude='52.520008',
                ort=f'Test City {i}',
                land='Test State',
                kreis='Test District',
                strasse=f'Test Street {i}',
                plz=10178,
                amt='Test Amt',
                ablage=f'test_image_{i}.jpg',
                beschreibung=self.test_description.id
            )
            session.add(location)
            session.flush()
            
            sighting = TblMeldungen(
                dat_fund_von=datetime.now().date() - timedelta(days=i),
                dat_meld=datetime.now().date(),
                fo_zuordnung=location.id,
                art_m=1,
                art_w=0,
                art_n=0,
                art_o=0,
                anm_melder=f'Test sighting {i}',
                deleted=False,
                bearb_id=None
            )
            session.add(sighting)
        
        session.commit()
        
        # Test first page - need to include required params
        response = client.get('/reviewer/9999?page=1&per_page=10&statusInput=offen&sort_order=id_desc')
        assert response.status_code == 200
        
        # Test second page - need to include required params
        response = client.get('/reviewer/9999?page=2&per_page=10&statusInput=offen&sort_order=id_desc')
        assert response.status_code == 200

    def test_error_handling_for_invalid_sighting_id(self, client):
        """Test error handling when sighting ID doesn't exist."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = '9999'
        
        # Test with non-existent ID
        response = client.post('/delete_sighting/99999')
        assert response.status_code == 404
        
        response = client.get('/get_sighting/99999')
        assert response.status_code == 404