"""Test ID consistency across different views of the application."""
import pytest
import json
from datetime import datetime
from bs4 import BeautifulSoup
from app.database.models import TblMeldungen, TblFundorte, TblUsers, TblMeldungUser


class TestIDConsistency:
    """Test that IDs are displayed consistently across different views."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, session):
        """Create test data with known IDs."""
        # Create test user
        self.test_user = TblUsers(
            user_id='test_user_123',
            user_name='Test User',
            user_kontakt='test@example.com',
            user_rolle='1'
        )
        session.add(self.test_user)
        
        # Create reviewer
        self.reviewer = TblUsers(
            user_id='reviewer_456',
            user_name='Test Reviewer',
            user_kontakt='reviewer@example.com',
            user_rolle='9'
        )
        session.add(self.reviewer)
        
        # Create test location
        self.location = TblFundorte(
            mtb='3644',
            longitude='13.404954',
            latitude='52.520008',
            ort='Test City',
            land='BB',
            kreis='Test District',
            strasse='Test Street',
            plz=10178,
            amt='Test Amt',
            ablage='test.jpg',
            beschreibung=1
        )
        session.add(self.location)
        session.flush()
        
        # Create approved sighting
        self.sighting = TblMeldungen(
            dat_fund_von=datetime.now().date(),
            dat_meld=datetime.now().date(),
            fo_zuordnung=self.location.id,
            dat_bear=datetime.now(),  # Approved
            bearb_id=self.reviewer.user_id,
            deleted=False,
            art_m=1,
            anm_melder='Test sighting for ID consistency'
        )
        session.add(self.sighting)
        session.flush()
        
        # Create user-sighting relation
        self.relation = TblMeldungUser(
            id_meldung=self.sighting.id,
            id_user=self.test_user.id
        )
        session.add(self.relation)
        
        session.commit()
        
        # Store the actual database ID for verification
        self.expected_report_id = self.sighting.id

    def test_map_view_shows_correct_id(self, client):
        """Test that map view shows the correct report ID."""
        response = client.get('/auswertungen')
        assert response.status_code == 200
        
        # Parse the HTML
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Find the reports JSON in the script
        script_tags = soup.find_all('script')
        reports_json = None
        
        for script in script_tags:
            if script.string and 'var reports = JSON.parse(' in script.string:
                start = script.string.find("JSON.parse('") + len("JSON.parse('")
                end = script.string.find("');", start)
                json_str = script.string[start:end]
                json_str = json_str.encode().decode('unicode_escape')
                reports_json = json.loads(json_str)
                break
        
        assert reports_json is not None, "Could not find reports JSON"
        
        # Find our test report
        our_report = None
        for report in reports_json:
            if report['report_id'] == self.expected_report_id:
                our_report = report
                break
        
        assert our_report is not None, f"Report with ID {self.expected_report_id} not found in map data"
        assert our_report['report_id'] == self.expected_report_id

    def test_admin_view_shows_correct_id(self, client):
        """Test that admin view shows the correct report ID."""
        with client.session_transaction() as sess:
            sess['user_id'] = self.reviewer.user_id
        
        response = client.get(f'/reviewer/{self.reviewer.user_id}?statusInput=all&sort_order=id_desc')
        assert response.status_code == 200
        
        # Check that the report ID appears in the response
        response_text = response.data.decode('utf-8')
        
        # The ID should appear as a badge and in data attributes
        assert str(self.expected_report_id) in response_text, f"Report ID {self.expected_report_id} not found in admin view"

    def test_provider_view_shows_correct_id(self, client):
        """Test that provider/melder view shows the correct report ID."""
        response = client.get(f'/report/{self.test_user.user_id}')
        assert response.status_code == 200
        
        response_text = response.data.decode('utf-8')
        
        # The ID should appear in the provider view
        assert str(self.expected_report_id) in response_text, f"Report ID {self.expected_report_id} not found in provider view"

    def test_marker_data_endpoint_returns_correct_id(self, client):
        """Test that the marker data endpoint returns the correct ID."""
        response = client.get(f'/get_marker_data/{self.expected_report_id}')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['id'] == self.expected_report_id, f"Marker data returned ID {data['id']}, expected {self.expected_report_id}"

    def test_id_terminology_consistency(self, client):
        """Test that ID terminology is consistent across views."""
        # Check map popup terminology
        response = client.get(f'/get_marker_data/{self.expected_report_id}')
        data = json.loads(response.data)
        assert 'id' in data, "Marker data should contain 'id' field"
        
        # Check provider view terminology
        response = client.get(f'/report/{self.test_user.user_id}')
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Look for "Melde-ID" text
        melde_id_text = soup.find(string=lambda text: text and 'Melde-ID' in text)
        assert melde_id_text is not None, "Provider view should show 'Melde-ID'"

    def test_no_internal_ids_exposed(self, client):
        """Test that internal database IDs are not exposed."""
        # Test that the alldata view doesn't expose sensitive internal IDs
        with client.session_transaction() as sess:
            sess['user_id'] = self.reviewer.user_id
        
        # Check the get_table_data endpoint which might expose internal IDs
        response = client.get('/admin/get_table_data/all_data_view?page=1&per_page=100')
        if response.status_code == 200:
            data = json.loads(response.data)
            
            # Check that sensitive columns are excluded
            if 'columns' in data:
                sensitive_columns = ['id_user', 'id_finder', 'fundorte_id', 'beschreibung_id']
                for col in sensitive_columns:
                    assert col not in data['columns'], f"Sensitive column {col} should not be exposed"
            
            # Verify that only safe IDs are shown
            # meldungen_id is the report ID (OK to show)
            # user_id is the public user identifier string (OK to show)
            allowed_id_columns = ['meldungen_id', 'user_id']
            for col in data.get('columns', []):
                if 'id' in col.lower() and col not in allowed_id_columns:
                    assert False, f"Unexpected ID column exposed: {col}"

    def test_database_view_uses_consistent_naming(self, client):
        """Test that database view uses consistent ID naming."""
        with client.session_transaction() as sess:
            sess['user_id'] = self.reviewer.user_id
        
        response = client.get('/alldata')
        assert response.status_code == 200
        
        # Check for API endpoint
        response = client.get('/admin/get_table_data/all_data_view?page=1&per_page=10')
        if response.status_code == 200:
            data = json.loads(response.data)
            
            # Check column names
            if 'columns' in data:
                # The materialized view uses 'meldungen_id' internally
                assert 'meldungen_id' in data['columns'] or 'id' in data['columns'], \
                    "Database view should have consistent ID column naming"

    def test_id_display_format_consistency(self, client):
        """Test that IDs are displayed in consistent format (no prefixes, just numbers)."""
        # Check various views to ensure IDs are shown as plain numbers
        views_to_check = [
            (f'/report/{self.test_user.user_id}', 'provider'),
            (f'/get_marker_data/{self.expected_report_id}', 'marker_data')
        ]
        
        for url, view_name in views_to_check:
            response = client.get(url)
            if response.status_code == 200:
                response_text = response.data.decode('utf-8')
                
                # Ensure the ID appears as a plain number
                assert str(self.expected_report_id) in response_text, \
                    f"Report ID should appear as plain number in {view_name} view"
                
                # Ensure no weird prefixes like "ID-" or "Report#"
                assert f"ID-{self.expected_report_id}" not in response_text, \
                    f"ID should not have 'ID-' prefix in {view_name} view"
                assert f"Report#{self.expected_report_id}" not in response_text, \
                    f"ID should not have 'Report#' prefix in {view_name} view"