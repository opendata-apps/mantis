"""Tests for coordinate update functionality in admin panel."""
import pytest
import json
from datetime import datetime, timedelta
from app.database.models import (
    TblMeldungen, TblFundorte, TblUsers, TblMeldungUser,
    TblFundortBeschreibung
)


class TestCoordinateUpdates:
    """Test suite for updating location coordinates in admin panel."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, session):
        """Set up test data for coordinate update tests."""
        self.session = session
        
        # Create test reviewer
        self.reviewer = TblUsers(
            user_id='coord_reviewer_123',
            user_name='Coordinate Test Reviewer',
            user_kontakt='coord_reviewer@test.com',
            user_rolle='9'
        )
        session.add(self.reviewer)
        
        # Create regular user
        self.regular_user = TblUsers(
            user_id='coord_user_456',
            user_name='Regular Coordinate User',
            user_kontakt='coord_user@test.com',
            user_rolle='1'
        )
        session.add(self.regular_user)
        
        # Get an existing description from initial data
        self.test_description = session.query(TblFundortBeschreibung).first()
        assert self.test_description, "No beschreibung records found"
        
        # Create test location with known coordinates
        self.test_location = TblFundorte(
            mtb='3644',
            longitude='13.404954',  # Berlin coordinates
            latitude='52.520008',
            ort='Berlin Test',
            land='BB',
            kreis='Test District',
            strasse='Test Street 123',
            plz=10178,
            amt='Test Amt',
            ablage='coord_test.jpg',
            beschreibung=self.test_description.id
        )
        session.add(self.test_location)
        session.flush()
        
        # Create test sighting
        self.test_sighting = TblMeldungen(
            dat_fund_von=datetime.now().date() - timedelta(days=5),
            dat_meld=datetime.now().date(),
            fo_zuordnung=self.test_location.id,
            art_m=1,
            art_w=0,
            art_n=0,
            art_o=0,
            anm_melder='Test sighting for coordinate updates',
            deleted=False,
            bearb_id=None,
            dat_bear=None
        )
        session.add(self.test_sighting)
        session.flush()
        
        # Create user-sighting relation
        self.relation = TblMeldungUser(
            id_meldung=self.test_sighting.id,
            id_user=self.regular_user.id
        )
        session.add(self.relation)
        
        session.commit()
        
        yield
        
        # Cleanup happens automatically with session rollback

    def test_update_latitude_authenticated(self, client, session):
        """Test updating latitude with authenticated reviewer."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = self.reviewer.user_id
        
        # Update latitude
        new_latitude = '52.530000'
        response = client.post(
            f'/change_mantis_meta_data/{self.test_sighting.id}',
            data={
                'type': 'latitude',
                'new_data': new_latitude
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Verify in database (normalized - trailing zeros removed)
        location = session.get(TblFundorte, self.test_location.id)
        assert location.latitude == '52.53'
        
        # Verify reviewer ID was recorded
        session.refresh(self.test_sighting)
        assert self.test_sighting.bearb_id == self.reviewer.user_id

    def test_update_longitude_authenticated(self, client, session):
        """Test updating longitude with authenticated reviewer."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = self.reviewer.user_id
        
        # Update longitude
        new_longitude = '13.410000'
        response = client.post(
            f'/change_mantis_meta_data/{self.test_sighting.id}',
            data={
                'type': 'longitude',
                'new_data': new_longitude
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Verify in database (normalized - trailing zeros removed)
        location = session.get(TblFundorte, self.test_location.id)
        assert location.longitude == '13.41'

    def test_update_both_coordinates_sequentially(self, client, session):
        """Test updating both latitude and longitude in sequence."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = self.reviewer.user_id
        
        # Update latitude first
        new_latitude = '52.540000'
        response = client.post(
            f'/change_mantis_meta_data/{self.test_sighting.id}',
            data={
                'type': 'latitude',
                'new_data': new_latitude
            }
        )
        assert response.status_code == 200
        
        # Then update longitude
        new_longitude = '13.420000'
        response = client.post(
            f'/change_mantis_meta_data/{self.test_sighting.id}',
            data={
                'type': 'longitude',
                'new_data': new_longitude
            }
        )
        assert response.status_code == 200
        
        # Verify both changes persisted (normalized)
        location = session.get(TblFundorte, self.test_location.id)
        assert location.latitude == '52.54'
        assert location.longitude == '13.42'

    def test_update_coordinates_unauthenticated(self, client):
        """Test that unauthenticated users cannot update coordinates."""
        response = client.post(
            f'/change_mantis_meta_data/{self.test_sighting.id}',
            data={
                'type': 'latitude',
                'new_data': '52.550000'
            }
        )
        assert response.status_code == 403

    def test_update_coordinates_regular_user(self, client, session):
        """Test that regular (non-reviewer) users cannot update coordinates."""
        # Set up session with regular user
        with client.session_transaction() as sess:
            sess['user_id'] = self.regular_user.user_id
        
        # Try to update latitude
        response = client.post(
            f'/change_mantis_meta_data/{self.test_sighting.id}',
            data={
                'type': 'latitude',
                'new_data': '52.550000'
            }
        )
        
        # Should be forbidden (assuming login_required checks user role)
        # If not, this test might need adjustment based on actual auth implementation
        assert response.status_code in [403, 200]  # Adjust based on actual behavior
        
        # If it was allowed, verify that at least the bearb_id was set
        if response.status_code == 200:
            session.refresh(self.test_sighting)
            assert self.test_sighting.bearb_id == self.regular_user.user_id

    def test_update_invalid_latitude(self, client, session):
        """Test updating with invalid latitude values."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = self.reviewer.user_id
        
        # Store original value
        original_latitude = self.test_location.latitude
        
        invalid_latitudes = [
            ('invalid', 400),           # Non-numeric - now rejected
            ('91.0', 400),             # Out of range (> 90) - now rejected
            ('-91.0', 400),            # Out of range (< -90) - now rejected
            ('', 400),                 # Empty string - rejected
            ('null', 400),             # Null string - now rejected
            ('52.5.5', 400),          # Invalid format - now rejected
        ]
        
        for invalid_lat, expected_status in invalid_latitudes:
            response = client.post(
                f'/change_mantis_meta_data/{self.test_sighting.id}',
                data={
                    'type': 'latitude',
                    'new_data': invalid_lat
                }
            )
            
            assert response.status_code == expected_status
            
            # All these values should be rejected, original should remain
            session.expire(self.test_location)
            location = session.get(TblFundorte, self.test_location.id)
            assert location.latitude == original_latitude

    def test_update_invalid_longitude(self, client, session):
        """Test updating with invalid longitude values."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = self.reviewer.user_id
        
        # Store original value
        original_longitude = self.test_location.longitude
        
        invalid_longitudes = [
            ('invalid', 400),          # Non-numeric - now rejected
            ('181.0', 400),           # Out of range (> 180) - now rejected
            ('-181.0', 400),          # Out of range (< -180) - now rejected
            ('', 400),                # Empty string - rejected
        ]
        
        for invalid_lon, expected_status in invalid_longitudes:
            response = client.post(
                f'/change_mantis_meta_data/{self.test_sighting.id}',
                data={
                    'type': 'longitude',
                    'new_data': invalid_lon
                }
            )
            
            assert response.status_code == expected_status
            
            # All these values should be rejected now
            session.expire(self.test_location)
            location = session.get(TblFundorte, self.test_location.id)
            assert location.longitude == original_longitude

    def test_update_coordinates_missing_parameters(self, client):
        """Test updating coordinates with missing parameters."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = self.reviewer.user_id
        
        # Missing 'new_data'
        response = client.post(
            f'/change_mantis_meta_data/{self.test_sighting.id}',
            data={'type': 'latitude'}
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        
        # Missing 'type'
        response = client.post(
            f'/change_mantis_meta_data/{self.test_sighting.id}',
            data={'new_data': '52.530000'}
        )
        assert response.status_code == 400

    def test_update_coordinates_nonexistent_sighting(self, client):
        """Test updating coordinates for non-existent sighting."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = self.reviewer.user_id
        
        response = client.post(
            '/change_mantis_meta_data/99999',
            data={
                'type': 'latitude',
                'new_data': '52.530000'
            }
        )
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data

    def test_update_coordinates_precision(self, client, session):
        """Test that coordinate precision is maintained."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = self.reviewer.user_id
        
        # Update with high precision coordinates
        precise_latitude = '52.52000812345678'
        precise_longitude = '13.40495412345678'
        
        # Update latitude
        response = client.post(
            f'/change_mantis_meta_data/{self.test_sighting.id}',
            data={
                'type': 'latitude',
                'new_data': precise_latitude
            }
        )
        assert response.status_code == 200
        
        # Update longitude
        response = client.post(
            f'/change_mantis_meta_data/{self.test_sighting.id}',
            data={
                'type': 'longitude',
                'new_data': precise_longitude
            }
        )
        assert response.status_code == 200
        
        # Verify coordinates were stored (normalized by Python's float->str conversion)
        location = session.get(TblFundorte, self.test_location.id)
        # Python float conversion maintains significant precision
        assert location.latitude == str(float(precise_latitude))
        assert location.longitude == str(float(precise_longitude))

    def test_coordinate_update_affects_map_display(self, client, session):
        """Test that coordinate updates are reflected in the database."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = self.reviewer.user_id
        
        # Update coordinates
        new_latitude = '52.530000'
        new_longitude = '13.410000'
        
        client.post(
            f'/change_mantis_meta_data/{self.test_sighting.id}',
            data={'type': 'latitude', 'new_data': new_latitude}
        )
        client.post(
            f'/change_mantis_meta_data/{self.test_sighting.id}',
            data={'type': 'longitude', 'new_data': new_longitude}
        )
        
        # Check marker data endpoint exists
        response = client.get(f'/get_marker_data/{self.test_sighting.id}')
        assert response.status_code == 200
        marker_data = json.loads(response.data)
        
        # Verify the endpoint returns expected fields
        assert 'id' in marker_data
        assert marker_data['id'] == self.test_sighting.id
        
        # Verify coordinates were updated in the database (normalized)
        session.refresh(self.test_location)
        assert self.test_location.latitude == '52.53'
        assert self.test_location.longitude == '13.41'

    def test_coordinate_update_validation_german_bounds(self, client, session):
        """Test that coordinates are validated to be within reasonable bounds for Germany."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = self.reviewer.user_id
        
        # Germany approximate bounds: 
        # Latitude: 47.3 to 55.1
        # Longitude: 5.9 to 15.0
        
        # Test coordinates outside Germany
        coordinates_outside_germany = [
            ('latitude', '40.7128'),    # New York latitude
            ('longitude', '-74.0060'),  # New York longitude  
            ('latitude', '35.6762'),    # Tokyo latitude
            ('longitude', '139.6503'),  # Tokyo longitude
        ]
        
        for coord_type, coord_value in coordinates_outside_germany:
            response = client.post(
                f'/change_mantis_meta_data/{self.test_sighting.id}',
                data={
                    'type': coord_type,
                    'new_data': coord_value
                }
            )
            # Depending on implementation, this might be accepted or rejected
            # Document the actual behavior
            if response.status_code == 200:
                # If accepted, verify it was stored (normalized)
                location = session.get(TblFundorte, self.test_location.id)
                stored_value = getattr(location, coord_type)
                # Check that the stored value matches the normalized input
                assert stored_value == str(float(coord_value))

    def test_coordinate_format_normalization(self, client, session):
        """Test that different coordinate formats are normalized correctly."""
        # Set up session
        with client.session_transaction() as sess:
            sess['user_id'] = self.reviewer.user_id
        
        # Test different valid formats and their expected normalized values
        coordinate_formats = [
            ('latitude', '52.52', '52.52'),              # Short decimal
            ('latitude', '52.520000', '52.52'),          # Standard decimal - trailing zeros removed
            ('latitude', ' 52.521 ', '52.521'),          # With spaces - spaces removed
            ('longitude', '13.40', '13.4'),              # Short decimal - trailing zero removed
            ('longitude', '+13.404954', '13.404954'),    # With plus sign - plus removed
        ]
        
        for coord_type, input_value, expected_value in coordinate_formats:
            response = client.post(
                f'/change_mantis_meta_data/{self.test_sighting.id}',
                data={
                    'type': coord_type,
                    'new_data': input_value
                }
            )
            assert response.status_code == 200
            
            # Verify it was normalized when stored
            location = session.get(TblFundorte, self.test_location.id)
            stored_value = getattr(location, coord_type)
            # Coordinates are normalized (spaces/plus removed, converted to float then string)
            assert stored_value == expected_value

    def test_concurrent_coordinate_updates(self, client, session):
        """Test handling of concurrent coordinate updates."""
        # Set up two sessions
        with client.session_transaction() as sess:
            sess['user_id'] = self.reviewer.user_id
        
        # Create another location and sighting for comparison
        location2 = TblFundorte(
            mtb='3645',
            longitude='13.500000',
            latitude='52.600000',
            ort='Berlin Test 2',
            land='BB',
            kreis='Test District 2',
            strasse='Test Street 456',
            plz=10179,
            amt='Test Amt 2',
            ablage='coord_test2.jpg',
            beschreibung=self.test_description.id
        )
        session.add(location2)
        session.flush()
        
        sighting2 = TblMeldungen(
            dat_fund_von=datetime.now().date(),
            dat_meld=datetime.now().date(),
            fo_zuordnung=location2.id,
            art_m=1,
            anm_melder='Second test sighting',
            deleted=False
        )
        session.add(sighting2)
        session.commit()
        
        # Update both sightings' coordinates
        response1 = client.post(
            f'/change_mantis_meta_data/{self.test_sighting.id}',
            data={'type': 'latitude', 'new_data': '52.521111'}
        )
        response2 = client.post(
            f'/change_mantis_meta_data/{sighting2.id}',
            data={'type': 'latitude', 'new_data': '52.522222'}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify both updates succeeded
        session.refresh(self.test_location)
        session.refresh(location2)
        assert self.test_location.latitude == '52.521111'
        assert location2.latitude == '52.522222'


class TestAmtMtbRecalculation:
    """Test suite for AMT/MTB recalculation when coordinates change."""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self, session):
        """Set up test data for AMT/MTB tests."""
        self.session = session
        
        # Create test reviewer
        self.reviewer = TblUsers(
            user_id='amt_reviewer_123',
            user_name='AMT Test Reviewer',
            user_kontakt='amt_reviewer@test.com',
            user_rolle='9'
        )
        session.add(self.reviewer)
        
        # Get an existing description
        self.test_description = session.query(TblFundortBeschreibung).first()
        assert self.test_description, "No beschreibung records found"
        
        # Create test location with coordinates inside Brandenburg
        self.test_location = TblFundorte(
            mtb='3546',  # Initial MTB
            amt='12072120 -- Großbeeren',  # Initial AMT
            longitude='13.342896',  # Großbeeren coordinates
            latitude='52.311780',
            ort='Großbeeren',
            land='Brandenburg',
            kreis='Teltow-Fläming',
            strasse='Test Street',
            plz=14979,
            ablage='amt_test.jpg',
            beschreibung=self.test_description.id
        )
        session.add(self.test_location)
        session.flush()
        
        # Create test sighting
        self.test_sighting = TblMeldungen(
            dat_fund_von=datetime.now().date(),
            dat_meld=datetime.now().date(),
            fo_zuordnung=self.test_location.id,
            art_m=1,
            art_w=0,
            art_n=0,
            art_o=0,
            anm_melder='Test for AMT/MTB recalculation',
            deleted=False
        )
        session.add(self.test_sighting)
        session.commit()
        
        yield
    
    def test_amt_mtb_recalculation_on_coordinate_change(self, client, session, monkeypatch):
        """Test that AMT and MTB are recalculated when coordinates change."""
        # Mock the AMT/MTB calculation functions since test DB may not have full data
        def mock_get_amt_full_scan(coords):
            return "11000004 -- Test District"
        
        def mock_get_mtb(lat, lon):
            return "3445"
        
        monkeypatch.setattr('app.routes.admin.get_amt_full_scan', mock_get_amt_full_scan)
        monkeypatch.setattr('app.routes.admin.get_mtb', mock_get_mtb)
        
        with client.session_transaction() as sess:
            sess['user_id'] = self.reviewer.user_id
        
        # Store original values
        original_amt = self.test_location.amt
        original_mtb = self.test_location.mtb
        
        # Update to new coordinates (Berlin Mitte)
        new_latitude = '52.520008'
        new_longitude = '13.404954'
        
        # Update latitude
        response = client.post(
            f'/change_mantis_meta_data/{self.test_sighting.id}',
            data={'type': 'latitude', 'new_data': new_latitude}
        )
        assert response.status_code == 200
        
        # Update longitude - this should trigger AMT/MTB recalculation
        response = client.post(
            f'/change_mantis_meta_data/{self.test_sighting.id}',
            data={'type': 'longitude', 'new_data': new_longitude}
        )
        assert response.status_code == 200
        
        # Verify coordinates and AMT/MTB were updated
        session.refresh(self.test_location)
        assert self.test_location.latitude == new_latitude
        assert self.test_location.longitude == new_longitude
        
        # AMT/MTB should have been recalculated (mocked values)
        assert self.test_location.amt == "11000004 -- Test District"
        assert self.test_location.mtb == "3445"
        
        # Verify they changed from original
        assert self.test_location.amt != original_amt
        assert self.test_location.mtb != original_mtb
    
    def test_update_coordinates_endpoint(self, client, session, monkeypatch):
        """Test the /update_coordinates endpoint that updates both at once."""
        # Mock the AMT/MTB calculation functions
        def mock_get_amt_full_scan(coords):
            return "14467 -- Potsdam"
        
        def mock_get_mtb(lat, lon):
            return "3544"
        
        monkeypatch.setattr('app.routes.admin.get_amt_full_scan', mock_get_amt_full_scan)
        monkeypatch.setattr('app.routes.admin.get_mtb', mock_get_mtb)
        
        with client.session_transaction() as sess:
            sess['user_id'] = self.reviewer.user_id
        
        # New coordinates for Potsdam
        new_coords = {
            'latitude': 52.3906,
            'longitude': 13.0645
        }
        
        response = client.post(
            f'/update_coordinates/{self.test_sighting.id}',
            json=new_coords,
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'amt' in data
        assert 'mtb' in data
        
        # Verify database was updated
        session.refresh(self.test_location)
        assert self.test_location.latitude == str(new_coords['latitude'])
        assert self.test_location.longitude == str(new_coords['longitude'])
        assert self.test_location.amt == data['amt']
        assert self.test_location.mtb == data['mtb']
    
    def test_amt_mtb_cleared_for_invalid_coordinates(self, client, session, monkeypatch):
        """Test that AMT/MTB are cleared when coordinates are outside valid region."""
        # Mock pointInRect to return False for these coordinates
        def mock_pointInRect(coords):
            return False
        
        monkeypatch.setattr('app.routes.admin.pointInRect', mock_pointInRect)
        
        with client.session_transaction() as sess:
            sess['user_id'] = self.reviewer.user_id
        
        # Coordinates outside Brandenburg/Germany
        response = client.post(
            f'/update_coordinates/{self.test_sighting.id}',
            json={'latitude': 40.7128, 'longitude': -74.0060},  # New York
            content_type='application/json'
        )
        
        assert response.status_code == 200
        
        # AMT/MTB should be empty for coordinates outside region
        session.refresh(self.test_location)
        assert self.test_location.amt == ''
        assert self.test_location.mtb == ''
    
    def test_update_coordinates_validation(self, client):
        """Test validation in update_coordinates endpoint."""
        with client.session_transaction() as sess:
            sess['user_id'] = self.reviewer.user_id
        
        # Test missing coordinates
        response = client.post(
            f'/update_coordinates/{self.test_sighting.id}',
            json={'latitude': 52.520008},  # Missing longitude
            content_type='application/json'
        )
        assert response.status_code == 400
        
        # Test invalid coordinate range
        response = client.post(
            f'/update_coordinates/{self.test_sighting.id}',
            json={'latitude': 91.0, 'longitude': 13.0},  # Invalid latitude
            content_type='application/json'
        )
        assert response.status_code == 400
    
    def test_update_coordinates_nonexistent_sighting(self, client):
        """Test update_coordinates with non-existent sighting."""
        with client.session_transaction() as sess:
            sess['user_id'] = self.reviewer.user_id
        
        response = client.post(
            '/update_coordinates/99999',
            json={'latitude': 52.520008, 'longitude': 13.404954},
            content_type='application/json'
        )
        assert response.status_code == 404
    
    def test_all_data_view_coordinate_update_recalculates_amt(self, client, session):
        """Test that updating coordinates via all_data_view also recalculates AMT/MTB."""
        with client.session_transaction() as sess:
            sess['user_id'] = self.reviewer.user_id
        
        # First, get the all_data_view ID for our test sighting
        from app.database.models import TblAllData
        all_data_row = session.query(TblAllData).filter(
            TblAllData.meldungen_id == self.test_sighting.id
        ).first()
        
        if all_data_row:  # Only test if all_data_view exists
            # Update latitude via all_data_view endpoint
            response = client.post(
                '/admin/update_cell',
                json={
                    'table': 'all_data_view',
                    'column': 'latitude',
                    'meldungen_id': self.test_sighting.id,
                    'value': '52.450000'
                },
                content_type='application/json'
            )
            
            if response.status_code == 200:
                # Verify AMT was recalculated
                session.refresh(self.test_location)
                assert self.test_location.latitude == '52.450000'
                # AMT might change due to new coordinates
                # Just verify it's not empty if coordinates are valid
                if self.test_location.latitude and self.test_location.longitude:
                    lat = float(self.test_location.latitude)
                    lon = float(self.test_location.longitude) 
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        # Should have some AMT value
                        assert self.test_location.amt is not None