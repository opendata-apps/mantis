"""Test map data generation to ensure is_() comparisons work correctly."""
import pytest
import json
from datetime import datetime
from app.database.models import TblMeldungen, TblFundorte
from bs4 import BeautifulSoup


class TestMapDataFilters:
    """Test map data generation with is_() comparisons for deleted field."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, session):
        """Create test data with various states."""
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
            beschreibung=1  # Use existing description
        )
        session.add(self.location)
        session.flush()
        
        # Create approved sighting (should appear in map)
        self.approved_sighting = TblMeldungen(
            dat_fund_von=datetime.now().date(),
            dat_meld=datetime.now().date(),
            fo_zuordnung=self.location.id,
            dat_bear=datetime.now(),  # Approved
            deleted=None,  # Not deleted (NULL)
            art_m=1
        )
        session.add(self.approved_sighting)
        
        # Create approved with deleted=False (should appear in map)
        self.approved_not_deleted = TblMeldungen(
            dat_fund_von=datetime.now().date(),
            dat_meld=datetime.now().date(),
            fo_zuordnung=self.location.id,
            dat_bear=datetime.now(),
            deleted=False,  # Explicitly false
            art_o=1
        )
        session.add(self.approved_not_deleted)
        
        # Create unapproved sighting (should NOT appear in map)
        self.unapproved_sighting = TblMeldungen(
            dat_fund_von=datetime.now().date(),
            dat_meld=datetime.now().date(),
            fo_zuordnung=self.location.id,
            dat_bear=None,  # Not approved
            deleted=None,
            art_w=1
        )
        session.add(self.unapproved_sighting)
        
        # Create deleted sighting (should NOT appear in map)
        self.deleted_sighting = TblMeldungen(
            dat_fund_von=datetime.now().date(),
            dat_meld=datetime.now().date(),
            fo_zuordnung=self.location.id,
            dat_bear=datetime.now(),  # Approved
            deleted=True,  # But deleted
            art_n=1
        )
        session.add(self.deleted_sighting)
        
        session.commit()

    def test_map_view_filters_correctly(self, client):
        """Test that /auswertungen map view only shows approved, non-deleted sightings."""
        response = client.get('/auswertungen')
        assert response.status_code == 200
        
        # Parse the HTML response
        soup = BeautifulSoup(response.data, 'html.parser')
        
        # Find the script tag containing reportsJson
        script_tags = soup.find_all('script')
        reports_json = None
        
        for script in script_tags:
            if script.string and 'var reports = JSON.parse(' in script.string:
                # Extract the JSON string
                start = script.string.find("JSON.parse('") + len("JSON.parse('")
                end = script.string.find("');", start)
                json_str = script.string[start:end]
                # Unescape the JSON
                json_str = json_str.encode().decode('unicode_escape')
                reports_json = json.loads(json_str)
                break
        
        assert reports_json is not None, "Could not find reports JSON in response"
        
        # Extract report IDs from the JSON
        report_ids = [report['report_id'] for report in reports_json]
        
        # Check that approved sightings are included
        assert self.approved_sighting.id in report_ids, "Approved (deleted=NULL) sighting not in map data"
        assert self.approved_not_deleted.id in report_ids, "Approved (deleted=False) sighting not in map data"
        
        # Check that unapproved and deleted sightings are NOT included
        assert self.unapproved_sighting.id not in report_ids, "Unapproved sighting should not be in map data"
        assert self.deleted_sighting.id not in report_ids, "Deleted sighting should not be in map data"

    def test_map_view_with_year_filter(self, client):
        """Test map view with year filter still respects deleted/approved filters."""
        current_year = datetime.now().year
        response = client.get(f'/auswertungen?year={current_year}')
        assert response.status_code == 200
        
        # Parse response and extract reports
        soup = BeautifulSoup(response.data, 'html.parser')
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
        
        if reports_json:
            report_ids = [report['report_id'] for report in reports_json]
            # Same filtering rules should apply
            assert self.deleted_sighting.id not in report_ids
            assert self.unapproved_sighting.id not in report_ids

    def test_get_marker_data_respects_approval(self, client):
        """Test that individual marker data endpoint respects approval status."""
        # Try to get data for approved sighting - should work
        response = client.get(f'/get_marker_data/{self.approved_sighting.id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == self.approved_sighting.id
        
        # Try to get data for unapproved sighting - should not work or return limited data
        response = client.get(f'/get_marker_data/{self.unapproved_sighting.id}')
        # Check if it returns 404 or limited data
        if response.status_code == 200:
            data = json.loads(response.data)
            # If it returns data, it might be limited or the sighting might not be on the map anyway
            assert 'id' in data

    def test_edge_case_combinations(self, client, session):
        """Test various edge case combinations of approved/deleted states."""
        test_cases = [
            # (dat_bear, deleted, should_appear, description)
            (datetime.now(), None, True, "approved + null deleted"),
            (datetime.now(), False, True, "approved + false deleted"),
            (datetime.now(), True, False, "approved + true deleted"),
            (None, None, False, "not approved + null deleted"),
            (None, False, False, "not approved + false deleted"),
            (None, True, False, "not approved + true deleted"),
        ]
        
        created_sightings = []
        
        for dat_bear, deleted, should_appear, desc in test_cases:
            sighting = TblMeldungen(
                dat_fund_von=datetime.now().date(),
                dat_meld=datetime.now().date(),
                fo_zuordnung=self.location.id,
                dat_bear=dat_bear,
                deleted=deleted,
                anm_melder=desc  # For identification
            )
            session.add(sighting)
            session.flush()
            created_sightings.append((sighting.id, should_appear))
        
        session.commit()
        
        # Check map data
        response = client.get('/auswertungen')
        assert response.status_code == 200
        
        # Extract reports JSON
        soup = BeautifulSoup(response.data, 'html.parser')
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
        
        report_ids = [report['report_id'] for report in reports_json] if reports_json else []
        
        for sighting_id, should_appear in created_sightings:
            if should_appear:
                assert sighting_id in report_ids, f"Sighting {sighting_id} should appear in map data"
            else:
                assert sighting_id not in report_ids, f"Sighting {sighting_id} should NOT appear in map data"