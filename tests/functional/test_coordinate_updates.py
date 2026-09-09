"""Tests for coordinate update functionality in admin panel."""

import pytest
import json
from datetime import datetime, timedelta
from sqlalchemy import select, func
from app.database.models import (
    TblMeldungen,
    TblFundorte,
    TblUsers,
    TblMeldungUser,
    TblFundortBeschreibung,
    ReportStatus,
)


class TestCoordinateUpdates:
    """Test suite for updating location coordinates in admin panel."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, session):
        """Set up test data for coordinate update tests."""
        self.session = session

        # Look up or create test reviewer
        self.reviewer = session.scalar(
            select(TblUsers).where(TblUsers.user_id == "coord_reviewer_123")
        )
        if not self.reviewer:
            self.reviewer = TblUsers(
                user_id="coord_reviewer_123",
                user_name="Coordinate Test Reviewer",
                user_kontakt="coord_reviewer@test.com",
                user_rolle="9",
            )
            session.add(self.reviewer)

        # Look up or create regular user
        self.regular_user = session.scalar(
            select(TblUsers).where(TblUsers.user_id == "coord_user_456")
        )
        if not self.regular_user:
            self.regular_user = TblUsers(
                user_id="coord_user_456",
                user_name="Regular Coordinate User",
                user_kontakt="coord_user@test.com",
                user_rolle="1",
            )
            session.add(self.regular_user)

        # Get an existing description from initial data
        self.test_description = session.scalar(select(TblFundortBeschreibung))
        assert self.test_description, "No beschreibung records found"

        # Create test location with known coordinates
        self.test_location = TblFundorte(
            mtb="3644",
            longitude="13.404954",  # Berlin coordinates
            latitude="52.520008",
            ort="Berlin Test",
            land="BB",
            kreis="Test District",
            strasse="Test Street 123",
            plz="10178",
            amt="Test Amt",
            ablage="coord_test.jpg",
            beschreibung=self.test_description.id,
        )
        session.add(self.test_location)
        session.flush()

        self.test_sighting = TblMeldungen(
            dat_fund_von=datetime.now().date() - timedelta(days=5),
            dat_meld=datetime.now().date(),
            fo_zuordnung=self.test_location.id,
            art_m=1,
            art_w=0,
            art_n=0,
            art_o=0,
            anm_melder="Test sighting for coordinate updates",
            bearb_id=None,
            dat_bear=None,
        )
        session.add(self.test_sighting)
        session.flush()

        # Create user-sighting relation
        self.relation = TblMeldungUser(
            id_meldung=self.test_sighting.id, id_user=self.regular_user.id
        )
        session.add(self.relation)

        session.commit()

        yield

    def test_update_latitude_authenticated(self, client, session):
        """Test updating latitude with authenticated reviewer."""
        with client.session_transaction() as sess:
            sess["_user_id"] = self.reviewer.user_id

        new_latitude = "52.530000"
        response = client.post(
            f"/change_mantis_meta_data/{self.test_sighting.id}",
            data={"type": "latitude", "new_data": new_latitude},
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True

        # Verify in database (normalized - trailing zeros removed)
        location = session.get(TblFundorte, self.test_location.id)
        assert location.latitude == 52.53

        # Verify reviewer ID was recorded
        session.refresh(self.test_sighting)
        assert self.test_sighting.bearb_id == self.reviewer.user_id

    def test_update_longitude_authenticated(self, client, session):
        """Test updating longitude with authenticated reviewer."""
        with client.session_transaction() as sess:
            sess["_user_id"] = self.reviewer.user_id

        new_longitude = "13.410000"
        response = client.post(
            f"/change_mantis_meta_data/{self.test_sighting.id}",
            data={"type": "longitude", "new_data": new_longitude},
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True

        # Verify in database (normalized - trailing zeros removed)
        location = session.get(TblFundorte, self.test_location.id)
        assert location.longitude == 13.41

    def test_update_both_coordinates_sequentially(self, client, session):
        """Test updating both latitude and longitude in sequence."""
        with client.session_transaction() as sess:
            sess["_user_id"] = self.reviewer.user_id

        # Update latitude first
        new_latitude = "52.540000"
        response = client.post(
            f"/change_mantis_meta_data/{self.test_sighting.id}",
            data={"type": "latitude", "new_data": new_latitude},
        )
        assert response.status_code == 200

        # Then update longitude
        new_longitude = "13.420000"
        response = client.post(
            f"/change_mantis_meta_data/{self.test_sighting.id}",
            data={"type": "longitude", "new_data": new_longitude},
        )
        assert response.status_code == 200

        # Verify both changes persisted (normalized)
        location = session.get(TblFundorte, self.test_location.id)
        assert location.latitude == 52.54
        assert location.longitude == 13.42

    def test_update_coordinates_unauthenticated(self, client):
        """Test that unauthenticated users cannot update coordinates."""
        response = client.post(
            f"/change_mantis_meta_data/{self.test_sighting.id}",
            data={"type": "latitude", "new_data": "52.550000"},
        )
        assert response.status_code == 403

    def test_update_coordinates_regular_user(self, client, session):
        """Test that regular (non-reviewer) users cannot update coordinates."""
        # Set up session with regular user
        with client.session_transaction() as sess:
            sess["_user_id"] = self.regular_user.user_id

        # Try to update latitude
        response = client.post(
            f"/change_mantis_meta_data/{self.test_sighting.id}",
            data={"type": "latitude", "new_data": "52.550000"},
        )

        # @reviewer_required aborts with 403 for non-reviewer users
        assert response.status_code == 403

    def test_update_invalid_latitude(self, client, session):
        """Test updating with invalid latitude values."""
        with client.session_transaction() as sess:
            sess["_user_id"] = self.reviewer.user_id

        # Store original value
        original_latitude = self.test_location.latitude

        invalid_latitudes = [
            ("invalid", 400),  # Non-numeric - now rejected
            ("91.0", 400),  # Out of range (> 90) - now rejected
            ("-91.0", 400),  # Out of range (< -90) - now rejected
            ("", 400),  # Empty string - rejected
            ("null", 400),  # Null string - now rejected
            ("52.5.5", 400),  # Invalid format - now rejected
        ]

        for invalid_lat, expected_status in invalid_latitudes:
            response = client.post(
                f"/change_mantis_meta_data/{self.test_sighting.id}",
                data={"type": "latitude", "new_data": invalid_lat},
            )

            assert response.status_code == expected_status

            # All these values should be rejected, original should remain
            session.expire(self.test_location)
            location = session.get(TblFundorte, self.test_location.id)
            assert location.latitude == original_latitude

    def test_update_invalid_longitude(self, client, session):
        """Test updating with invalid longitude values."""
        with client.session_transaction() as sess:
            sess["_user_id"] = self.reviewer.user_id

        # Store original value
        original_longitude = self.test_location.longitude

        invalid_longitudes = [
            ("invalid", 400),  # Non-numeric - now rejected
            ("181.0", 400),  # Out of range (> 180) - now rejected
            ("-181.0", 400),  # Out of range (< -180) - now rejected
            ("", 400),  # Empty string - rejected
        ]

        for invalid_lon, expected_status in invalid_longitudes:
            response = client.post(
                f"/change_mantis_meta_data/{self.test_sighting.id}",
                data={"type": "longitude", "new_data": invalid_lon},
            )

            assert response.status_code == expected_status

            # All these values should be rejected now
            session.expire(self.test_location)
            location = session.get(TblFundorte, self.test_location.id)
            assert location.longitude == original_longitude

    def test_update_coordinates_missing_parameters(self, client):
        """Test updating coordinates with missing parameters."""
        with client.session_transaction() as sess:
            sess["_user_id"] = self.reviewer.user_id

        # Missing 'new_data'
        response = client.post(
            f"/change_mantis_meta_data/{self.test_sighting.id}",
            data={"type": "latitude"},
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

        # Missing 'type'
        response = client.post(
            f"/change_mantis_meta_data/{self.test_sighting.id}",
            data={"new_data": "52.530000"},
        )
        assert response.status_code == 400

    def test_update_coordinates_nonexistent_sighting(self, client, session):
        """Test updating coordinates for non-existent sighting."""
        with client.session_transaction() as sess:
            sess["_user_id"] = self.reviewer.user_id

        missing_id = (session.scalar(select(func.max(TblMeldungen.id))) or 0) + 1
        response = client.post(
            f"/change_mantis_meta_data/{missing_id}",
            data={"type": "latitude", "new_data": "52.530000"},
        )
        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data

    def test_update_coordinates_precision(self, client, session):
        """Test that coordinate precision is maintained."""
        with client.session_transaction() as sess:
            sess["_user_id"] = self.reviewer.user_id

        # Update with high precision coordinates
        precise_latitude = "52.52000812345678"
        precise_longitude = "13.40495412345678"

        response = client.post(
            f"/change_mantis_meta_data/{self.test_sighting.id}",
            data={"type": "latitude", "new_data": precise_latitude},
        )
        assert response.status_code == 200

        response = client.post(
            f"/change_mantis_meta_data/{self.test_sighting.id}",
            data={"type": "longitude", "new_data": precise_longitude},
        )
        assert response.status_code == 200

        # Verify coordinates were stored (normalized by Python's float->str conversion)
        location = session.get(TblFundorte, self.test_location.id)
        # Python float conversion maintains significant precision
        assert location.latitude == float(precise_latitude)
        assert location.longitude == float(precise_longitude)

    def test_coordinate_update_affects_map_display(self, client, session):
        """Test that coordinate updates are reflected in the database."""
        # Marker endpoint only exposes approved sightings.
        self.test_sighting.statuses = [ReportStatus.APPR.value]
        self.test_sighting.dat_bear = datetime.now()
        session.commit()

        with client.session_transaction() as sess:
            sess["_user_id"] = self.reviewer.user_id

        # Update coordinates
        new_latitude = "52.530000"
        new_longitude = "13.410000"

        client.post(
            f"/change_mantis_meta_data/{self.test_sighting.id}",
            data={"type": "latitude", "new_data": new_latitude},
        )
        client.post(
            f"/change_mantis_meta_data/{self.test_sighting.id}",
            data={"type": "longitude", "new_data": new_longitude},
        )

        # Check marker data endpoint exists
        response = client.get(f"/get_marker_data/{self.test_sighting.id}")
        assert response.status_code == 200
        marker_data = json.loads(response.data)

        # Verify the endpoint returns expected fields
        assert "id" in marker_data
        assert marker_data["id"] == self.test_sighting.id

        # Verify coordinates were updated in the database (normalized)
        session.refresh(self.test_location)
        assert self.test_location.latitude == 52.53
        assert self.test_location.longitude == 13.41

    def test_coordinate_update_outside_germany_is_allowed(self, client, session):
        """Coordinates outside Germany are allowed; only spatial enrichment is skipped."""
        with client.session_transaction() as sess:
            sess["_user_id"] = self.reviewer.user_id

        coordinates_outside_germany = [
            ("latitude", "48.2082"),  # Wien latitude
            ("longitude", "16.3738"),  # Wien longitude
            ("latitude", "38.7223"),  # Lisboa latitude
            ("longitude", "-9.1393"),  # Lisboa longitude
        ]

        for coord_type, coord_value in coordinates_outside_germany:
            response = client.post(
                f"/change_mantis_meta_data/{self.test_sighting.id}",
                data={"type": coord_type, "new_data": coord_value},
            )
            assert response.status_code == 200

            location = session.get(
                TblFundorte, self.test_location.id, populate_existing=True
            )
            stored_value = getattr(location, coord_type)
            assert stored_value == float(coord_value)

    def test_coordinate_format_normalization(self, client, session):
        """Test that different coordinate formats are normalized correctly."""
        with client.session_transaction() as sess:
            sess["_user_id"] = self.reviewer.user_id

        # Test different valid formats and their expected normalized values
        coordinate_formats = [
            ("latitude", "52.52", "52.52"),  # Short decimal
            (
                "latitude",
                "52.520000",
                "52.52",
            ),  # Standard decimal - trailing zeros removed
            ("latitude", " 52.521 ", "52.521"),  # With spaces - spaces removed
            ("longitude", "13.40", "13.4"),  # Short decimal - trailing zero removed
            ("longitude", "+13.404954", "13.404954"),  # With plus sign - plus removed
        ]

        for coord_type, input_value, expected_value in coordinate_formats:
            response = client.post(
                f"/change_mantis_meta_data/{self.test_sighting.id}",
                data={"type": coord_type, "new_data": input_value},
            )
            assert response.status_code == 200

            # Verify it was normalized when stored
            location = session.get(
                TblFundorte, self.test_location.id, populate_existing=True
            )
            stored_value = getattr(location, coord_type)
            # Coordinates are parsed (spaces/plus removed) and stored as floats
            assert stored_value == float(expected_value)

    def test_updates_to_separate_reports_keep_their_own_coordinates(
        self, client, session
    ):
        """Editing a second report must not change the first report again."""
        with client.session_transaction() as sess:
            sess["_user_id"] = self.reviewer.user_id

        # Create another location and sighting for comparison
        location2 = TblFundorte(
            mtb="3645",
            longitude="13.500000",
            latitude="52.600000",
            ort="Berlin Test 2",
            land="BB",
            kreis="Test District 2",
            strasse="Test Street 456",
            plz="10179",
            amt="Test Amt 2",
            ablage="coord_test2.jpg",
            beschreibung=self.test_description.id,
        )
        session.add(location2)
        session.flush()

        sighting2 = TblMeldungen(
            dat_fund_von=datetime.now().date(),
            dat_meld=datetime.now().date(),
            fo_zuordnung=location2.id,
            art_m=1,
            anm_melder="Second test sighting",
        )
        session.add(sighting2)
        session.commit()

        # Update both sightings' coordinates
        response1 = client.post(
            f"/change_mantis_meta_data/{self.test_sighting.id}",
            data={"type": "latitude", "new_data": "52.521111"},
        )
        response2 = client.post(
            f"/change_mantis_meta_data/{sighting2.id}",
            data={"type": "latitude", "new_data": "52.522222"},
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Verify both updates succeeded
        session.refresh(self.test_location)
        session.refresh(location2)
        assert self.test_location.latitude == 52.521111
        assert location2.latitude == 52.522222


class TestAmtMtbRecalculation:
    """Test suite for AMT/MTB recalculation when coordinates change."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, session):
        """Set up test data for AMT/MTB tests."""
        self.session = session

        # Look up or create test reviewer
        self.reviewer = session.scalar(
            select(TblUsers).where(TblUsers.user_id == "amt_reviewer_123")
        )
        if not self.reviewer:
            self.reviewer = TblUsers(
                user_id="amt_reviewer_123",
                user_name="AMT Test Reviewer",
                user_kontakt="amt_reviewer@test.com",
                user_rolle="9",
            )
            session.add(self.reviewer)

        # Get an existing description
        self.test_description = session.scalar(select(TblFundortBeschreibung))
        assert self.test_description, "No beschreibung records found"

        # Create test location with coordinates inside Brandenburg
        self.test_location = TblFundorte(
            mtb="3546",  # Initial MTB
            amt="12072120 -- Großbeeren",  # Initial AMT
            longitude="13.342896",  # Großbeeren coordinates
            latitude="52.311780",
            ort="Großbeeren",
            land="Brandenburg",
            kreis="Teltow-Fläming",
            strasse="Test Street",
            plz="14979",
            ablage="amt_test.jpg",
            beschreibung=self.test_description.id,
        )
        session.add(self.test_location)
        session.flush()

        self.test_sighting = TblMeldungen(
            dat_fund_von=datetime.now().date(),
            dat_meld=datetime.now().date(),
            fo_zuordnung=self.test_location.id,
            art_m=1,
            art_w=0,
            art_n=0,
            art_o=0,
            anm_melder="Test for AMT/MTB recalculation",
        )
        session.add(self.test_sighting)
        session.commit()

        yield

    def test_amt_mtb_recalculation_on_coordinate_change(
        self, client, session, monkeypatch
    ):
        """Test that AMT and MTB are recalculated when coordinates change."""

        # Mock the AMT/MTB calculation functions since test DB may not have full data
        def mock_get_amt_enriched(coords):
            return {
                "ags": "11000004",
                "gen": "Test District",
                "land": "Berlin",
                "kreis": "Berlin",
                "amt_string": "11000004 -- Test District",
            }

        def mock_get_mtb(lat, lon):
            return "3445"

        monkeypatch.setattr(
            "app.tools.location_enrichment.get_amt_enriched", mock_get_amt_enriched
        )
        monkeypatch.setattr("app.tools.location_enrichment.get_mtb", mock_get_mtb)

        with client.session_transaction() as sess:
            sess["_user_id"] = self.reviewer.user_id

        # Store original values
        original_amt = self.test_location.amt
        original_mtb = self.test_location.mtb

        # Update to new coordinates (Berlin Mitte)
        new_latitude = "52.520008"
        new_longitude = "13.404954"

        response = client.post(
            f"/change_mantis_meta_data/{self.test_sighting.id}",
            data={"type": "latitude", "new_data": new_latitude},
        )
        assert response.status_code == 200

        # Update longitude - this should trigger AMT/MTB recalculation
        response = client.post(
            f"/change_mantis_meta_data/{self.test_sighting.id}",
            data={"type": "longitude", "new_data": new_longitude},
        )
        assert response.status_code == 200

        # Verify coordinates and AMT/MTB were updated
        session.refresh(self.test_location)
        assert self.test_location.latitude == float(new_latitude)
        assert self.test_location.longitude == float(new_longitude)

        # AMT/MTB should have been recalculated (mocked values)
        assert self.test_location.amt == "11000004 -- Test District"
        assert self.test_location.mtb == "3445"

        # Verify they changed from original
        assert self.test_location.amt != original_amt
        assert self.test_location.mtb != original_mtb

    def test_update_coordinates_endpoint(self, client, session, monkeypatch):
        """Test the /update_coordinates endpoint that updates both at once."""

        # Mock the AMT/MTB calculation functions
        def mock_get_amt_enriched(coords):
            return {
                "ags": "14467",
                "gen": "Potsdam",
                "land": "Brandenburg",
                "kreis": "Potsdam",
                "amt_string": "14467 -- Potsdam",
            }

        def mock_get_mtb(lat, lon):
            return "3544"

        monkeypatch.setattr(
            "app.tools.location_enrichment.get_amt_enriched", mock_get_amt_enriched
        )
        monkeypatch.setattr("app.tools.location_enrichment.get_mtb", mock_get_mtb)

        with client.session_transaction() as sess:
            sess["_user_id"] = self.reviewer.user_id

        # New coordinates for Potsdam
        new_coords = {"latitude": "52.3906", "longitude": "13.0645"}

        response = client.post(
            f"/update_coordinates/{self.test_sighting.id}",
            data=new_coords,
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "amt" in data
        assert "mtb" in data

        # Verify database was updated
        session.refresh(self.test_location)
        assert self.test_location.latitude == float(new_coords["latitude"])
        assert self.test_location.longitude == float(new_coords["longitude"])
        assert self.test_location.amt == data["amt"]
        assert self.test_location.mtb == data["mtb"]

    def test_amt_mtb_cleared_for_invalid_coordinates(self, app, client, session):
        """AMT/MTB are cleared for a coordinate outside Germany.

        Wien sits inside the MTB grid's bounding box, so the grid formula alone
        would hand it sheet 7764. The AGS polygon lookup is what actually knows
        the border, so no German Kreis means no Messtischblatt either.
        """
        from app.database.aemter_koordinaten import TblAemterCoordinaten
        from app.tools.gemeinde_finder import reload_gemeinde_cache

        # Carry our own polygon so the positive control holds even when an
        # earlier test has replaced the shared aemter table. Which polygon wins
        # the lookup depends on what else is loaded, so assert only that the
        # point resolves at all.
        area = TblAemterCoordinaten(
            ags=99999904,
            gen="Testgemeinde Elbe-Elster",
            properties={
                "type": "Polygon",
                "coordinates": [
                    [
                        [13.39, 51.78],
                        [13.42, 51.78],
                        [13.42, 51.80],
                        [13.39, 51.80],
                        [13.39, 51.78],
                    ]
                ],
            },
        )
        session.add(area)
        session.commit()
        with app.app_context():
            reload_gemeinde_cache()

        with client.session_transaction() as sess:
            sess["_user_id"] = self.reviewer.user_id

        try:
            # Inside the polygon: the Messtischblatt must be filled in. Without
            # this control the assertions below would also hold on a database
            # with no polygons at all, and the test would prove nothing.
            response = client.post(
                f"/update_coordinates/{self.test_sighting.id}",
                data={"latitude": "51.789314", "longitude": "13.405689"},
            )
            assert response.status_code == 200
            session.refresh(self.test_location)
            assert self.test_location.mtb == "4246"
            assert self.test_location.amt != ""

            response = client.post(
                f"/update_coordinates/{self.test_sighting.id}",
                data={"latitude": "48.2082", "longitude": "16.3738"},  # Wien
            )
            assert response.status_code == 200

            session.refresh(self.test_location)
            assert self.test_location.amt == ""
            assert self.test_location.mtb == ""
        finally:
            session.delete(area)
            session.commit()
            with app.app_context():
                reload_gemeinde_cache()

    def test_update_coordinates_validation(self, client):
        """Test validation in update_coordinates endpoint."""
        with client.session_transaction() as sess:
            sess["_user_id"] = self.reviewer.user_id

        # Test missing coordinates
        response = client.post(
            f"/update_coordinates/{self.test_sighting.id}",
            data={"latitude": "52.520008"},  # Missing longitude
        )
        assert response.status_code == 400

        # Test invalid coordinate range
        response = client.post(
            f"/update_coordinates/{self.test_sighting.id}",
            data={"latitude": "91.0", "longitude": "13.0"},  # Invalid latitude
        )
        assert response.status_code == 400

    def test_update_coordinates_nonexistent_sighting(self, client, session):
        """Test update_coordinates with non-existent sighting."""
        with client.session_transaction() as sess:
            sess["_user_id"] = self.reviewer.user_id

        missing_id = (session.scalar(select(func.max(TblMeldungen.id))) or 0) + 1
        response = client.post(
            f"/update_coordinates/{missing_id}",
            data={"latitude": "52.520008", "longitude": "13.404954"},
        )
        assert response.status_code == 404

    def test_all_data_view_coordinate_update_recalculates_amt(
        self, app, client, session
    ):
        from app.database.models import TblAemterCoordinaten
        from app.tools.gemeinde_finder import reload_gemeinde_cache

        area = TblAemterCoordinaten(
            ags=11000004,
            gen="Testgebiet",
            properties={
                "type": "Polygon",
                "coordinates": [
                    [
                        [13.40, 52.51],
                        [13.41, 52.51],
                        [13.41, 52.53],
                        [13.40, 52.53],
                        [13.40, 52.51],
                    ]
                ],
            },
        )
        self.test_location.longitude = 13.404954
        session.add(area)
        session.add(
            TblMeldungUser(id_meldung=self.test_sighting.id, id_user=self.reviewer.id)
        )
        session.commit()
        with app.app_context():
            reload_gemeinde_cache()
        with client.session_transaction() as sess:
            sess["_user_id"] = self.reviewer.user_id
        try:
            response = client.post(
                "/admin/update_cell",
                json={
                    "column": "latitude",
                    "meldungen_id": self.test_sighting.id,
                    "value": "52.520008",
                },
            )
            assert response.status_code == 200
            assert response.json == {"success": True}
            session.refresh(self.test_location)
            assert self.test_location.latitude == 52.520008
            assert self.test_location.longitude == 13.404954
            assert self.test_location.amt == "11000004 -- Testgebiet"
            assert self.test_location.mtb == "3446"
        finally:
            session.delete(area)
            session.commit()
            with app.app_context():
                reload_gemeinde_cache()
