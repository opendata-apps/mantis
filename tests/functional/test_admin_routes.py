"""Tests for admin routes including reviewer interface and data management."""

import pytest
from datetime import datetime, timedelta
import json
from sqlalchemy import select

from app.database.models import (
    TblMeldungen,
    TblFundorte,
    TblUsers,
    TblMeldungUser,
    TblFundortBeschreibung,
)


class TestAdminRoutes:
    """Test suite for admin and reviewer routes."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, session):
        """Set up test data for admin tests."""
        self.session = session

        # Create test user with reviewer role
        self.reviewer_user = TblUsers(
            user_id="9999",
            user_name="Test Reviewer",
            user_kontakt="reviewer@test.com",
            user_rolle="9",
        )
        session.add(self.reviewer_user)

        # Create regular user (non-reviewer)
        self.regular_user = TblUsers(
            user_id="1111",
            user_name="Regular User",
            user_kontakt="user@test.com",
            user_rolle="1",
        )
        session.add(self.regular_user)

        # Use an existing description from the pre-populated data
        self.test_description = session.scalar(
            select(TblFundortBeschreibung).where(TblFundortBeschreibung.id == 1)
        )
        if not self.test_description:
            # Fallback if somehow the initial data isn't there
            self.test_description = session.scalar(select(TblFundortBeschreibung))

        assert self.test_description, "No beschreibung records found in database"

        # Create test location
        self.test_location = TblFundorte(
            mtb="3644",
            longitude="13.404954",
            latitude="52.520008",
            ort="Test City",
            land="Test State",
            kreis="Test District",
            strasse="Test Street",
            plz=10178,
            amt="Test Amt",
            ablage="test_image.jpg",
            beschreibung=self.test_description.id,
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
            anm_melder="Test sighting",
            deleted=False,
            bearb_id=None,  # Not approved yet
            dat_bear=None,
        )
        session.add(self.test_sighting)
        session.flush()

        # Create user-sighting relation
        self.test_relation = TblMeldungUser(
            id_meldung=self.test_sighting.id, id_user=self.reviewer_user.id
        )
        session.add(self.test_relation)

        session.commit()

        # Ensure the materialized view reflects new rows used by admin APIs
        try:
            from app import db
            import app.database.alldata as ad

            ad.refresh_materialized_view(db)
        except Exception:
            # Tests that don't depend on the view can proceed; specific tests will fail if needed
            pass

        yield

        # Cleanup happens automatically with session rollback

    def test_reviewer_page_access_with_valid_reviewer(self, client):
        """Test that reviewers can access the reviewer page."""
        # Follow redirects to handle the automatic redirect to add default params
        response = client.get("/reviewer/9999", follow_redirects=True)
        assert response.status_code == 200
        # Check for admin panel content
        assert b"Admin Panel" in response.data or b"admin" in response.data.lower()
        # Check that session was set
        with client.session_transaction() as sess:
            assert sess.get("user_id") == "9999"

    def test_reviewer_page_access_with_invalid_user(self, client):
        """Test that non-reviewers cannot access the reviewer page."""
        # Non-existent user
        response = client.get("/reviewer/invalid")
        assert response.status_code == 403

        # Regular user (not reviewer)
        response = client.get("/reviewer/1111")
        assert response.status_code == 403

    def test_reviewer_page_filters(self, client):
        """Test filtering functionality on reviewer page."""
        # Test status filter
        response = client.get("/reviewer/9999?statusInput=offen&sort_order=id_desc")
        assert response.status_code == 200

        # Test with search query - need to include required params
        response = client.get(
            "/reviewer/9999?q=Test&search_type=full_text&statusInput=offen&sort_order=id_desc"
        )
        assert response.status_code == 200

        # Test date filters - need to include required params
        response = client.get(
            "/reviewer/9999?dateFrom=2024-01-01&dateTo=2024-12-31&statusInput=offen&sort_order=id_desc"
        )
        assert response.status_code == 200

    def test_reviewer_page_session_storage(self, client):
        """Test that user_id is stored in session when accessing reviewer page."""
        with client.session_transaction() as sess:
            assert "user_id" not in sess

        # Follow redirects
        response = client.get("/reviewer/9999", follow_redirects=True)
        assert response.status_code == 200

        with client.session_transaction() as sess:
            assert sess["user_id"] == "9999"

    def test_provider_view_preserves_reviewer_session(self, client):
        """Opening provider page should not override active reviewer auth session."""
        with client.session_transaction() as sess:
            sess["user_id"] = "9999"

        response = client.get("/report/1111")
        assert response.status_code == 200

        with client.session_transaction() as sess:
            assert sess["user_id"] == "9999"

    def test_sichtungen_alias_preserves_reviewer_session(self, client):
        """Alias route should also preserve active reviewer auth session."""
        with client.session_transaction() as sess:
            sess["user_id"] = "9999"

        response = client.get("/sichtungen/1111")
        assert response.status_code == 200

        with client.session_transaction() as sess:
            assert sess["user_id"] == "9999"

    def test_provider_view_sets_session_for_non_reviewer_context(self, client):
        """Provider link should still initialize session in non-reviewer context."""
        with client.session_transaction() as sess:
            sess.clear()

        response = client.get("/report/1111")
        assert response.status_code == 200

        with client.session_transaction() as sess:
            assert sess.get("user_id") == "1111"

    def test_provider_view_melden_button_uses_viewed_user_id(self, client):
        """Provider page CTA should target viewed reporter ID, not active session user."""
        with client.session_transaction() as sess:
            sess["user_id"] = "9999"  # Active reviewer session

        response = client.get("/report/1111")
        assert response.status_code == 200
        assert b'/melden/1111' in response.data

    def test_provider_view_does_not_render_reviewer_nav_links(self, client):
        """Provider page should not expose reviewer/statistics nav links for reporter context."""
        with client.session_transaction() as sess:
            sess.clear()

        response = client.get("/report/1111")
        assert response.status_code == 200
        assert b'/reviewer/1111' not in response.data
        assert b'/statistik/1111' not in response.data

    def test_toggle_approve_still_works_after_opening_provider_page(
        self, client, session
    ):
        """Reviewer should remain authorized for approve actions after provider page visit."""
        with client.session_transaction() as sess:
            sess["user_id"] = "9999"

        provider_response = client.get("/report/1111")
        assert provider_response.status_code == 200

        response = client.post(
            f"/toggle_approve_sighting/{self.test_sighting.id}",
            data={"filter_status": "all"},
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        assert b'id="report-card-' in response.data

        session.refresh(self.test_sighting)
        assert self.test_sighting.bearb_id == "9999"

    def test_change_mantis_metadata_authenticated(self, client, session):
        """Test changing mantis metadata with authentication."""
        # Set up session
        with client.session_transaction() as sess:
            sess["user_id"] = "9999"

        # Test changing location data - ort (city)
        response = client.post(
            f"/change_mantis_meta_data/{self.test_sighting.id}",
            data={"type": "ort", "new_data": "Updated City"},
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True

        # Verify the change in database
        location = session.get(TblFundorte, self.test_location.id)
        assert location.ort == "Updated City"

    def test_change_mantis_metadata_unauthenticated(self, client):
        """Test that unauthenticated users cannot change metadata."""
        response = client.post(
            f"/change_mantis_meta_data/{self.test_sighting.id}",
            data={"beschreibung": "2"},
        )
        assert response.status_code == 403

    def test_toggle_approve_sighting(self, client, session):
        """Test approving/unapproving sightings."""
        # Set up session
        with client.session_transaction() as sess:
            sess["user_id"] = "9999"

        # Initial state should be unapproved
        assert self.test_sighting.bearb_id is None
        assert self.test_sighting.dat_bear is None

        # Toggle to approve
        response = client.post(
            f"/toggle_approve_sighting/{self.test_sighting.id}",
            data={"filter_status": "all"},
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        assert b'id="report-card-' in response.data

        # Verify in database
        session.refresh(self.test_sighting)
        assert self.test_sighting.bearb_id == "9999"
        assert self.test_sighting.dat_bear is not None

    def test_toggle_approve_sighting_without_email(self, client, session):
        """Test that approving works even when email sending is disabled."""
        # Set up session
        with client.session_transaction() as sess:
            sess["user_id"] = "9999"

        # Approve sighting (emails are disabled in test config)
        response = client.post(
            f"/toggle_approve_sighting/{self.test_sighting.id}",
            data={"filter_status": "all"},
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        assert b"id=\"report-card-" in response.data

        # Verify approval happened
        session.refresh(self.test_sighting)
        assert self.test_sighting.bearb_id == "9999"
        assert self.test_sighting.dat_bear is not None

    def test_delete_sighting(self, client, session):
        """Test soft deleting a sighting."""
        # Set up session
        with client.session_transaction() as sess:
            sess["user_id"] = "9999"

        # Delete sighting
        response = client.post(
            f"/delete_sighting/{self.test_sighting.id}",
            data={"filter_status": "all"},
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        assert b"id=\"report-card-" in response.data

        # Verify soft delete in database
        session.refresh(self.test_sighting)
        assert self.test_sighting.deleted is True

    def test_undelete_sighting(self, client, session):
        """Test undeleting a soft-deleted sighting."""
        # Set up session
        with client.session_transaction() as sess:
            sess["user_id"] = "9999"

        # First delete the sighting
        self.test_sighting.statuses = ["DEL"]
        self.test_sighting.deleted = True
        session.commit()

        # Undelete sighting
        response = client.post(
            f"/undelete_sighting/{self.test_sighting.id}",
            data={"filter_status": "all"},
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        assert b"id=\"report-card-" in response.data

        # Verify undelete in database
        session.refresh(self.test_sighting)
        assert self.test_sighting.deleted is False

    def test_change_mantis_count(self, client, session):
        """Test changing mantis count fields."""
        # Set up session
        with client.session_transaction() as sess:
            sess["user_id"] = "9999"

        # Update male count
        response = client.post(
            f"/change_mantis_count/{self.test_sighting.id}",
            data={"type": "Männchen", "new_count": "2"},
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True

        # Verify in database
        session.refresh(self.test_sighting)
        assert self.test_sighting.art_m == 2

    def test_reviewer_page_uses_native_modal_and_fragment_assets(self, client):
        """Reviewer page should load native dialog + HTMX admin modules."""
        with client.session_transaction() as sess:
            sess["user_id"] = "9999"

        response = client.get(
            "/reviewer/9999?statusInput=offen&sort_order=id_desc",
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"admin-htmx" in response.data
        assert b"admin-modal" in response.data
        assert b'<dialog id="modal"' in response.data
        assert b"fetch('/get_sighting/" not in response.data

    def test_modal_open_route_renders_general_tab(self, client):
        """Initial modal endpoint should return modal open partial with general tab."""
        with client.session_transaction() as sess:
            sess["user_id"] = "9999"

        response = client.get(f"/modal/{self.test_sighting.id}?filter_status=offen")
        assert response.status_code == 200
        assert b'id="tab-content"' in response.data
        assert b"General Information" in response.data
        assert b'id="modal-actions"' in response.data

    def test_modal_location_tab_response_contains_oob_updates(self, client):
        """Location tab endpoint should return tab content plus OOB tab/action updates."""
        with client.session_transaction() as sess:
            sess["user_id"] = "9999"

        response = client.get(
            f"/modal/location/{self.test_sighting.id}?filter_status=offen"
        )
        assert response.status_code == 200
        assert b'id="map"' in response.data
        assert b'hx-swap-oob="outerHTML"' in response.data
        assert b'id="modal-actions"' in response.data

    def test_toggle_flag_returns_card_partial(self, client, session):
        """HTMX flag toggles should return updated card partial HTML."""
        with client.session_transaction() as sess:
            sess["user_id"] = "9999"

        response = client.post(
            f"/toggle_flag/{self.test_sighting.id}",
            data={"flag": "UNKL", "filter_status": "offen"},
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        assert b'id="report-card-' in response.data

        session.refresh(self.test_sighting)
        assert "UNKL" in (self.test_sighting.statuses or [])

    def test_toggle_flag_invalid_value(self, client):
        """Invalid flag values should be rejected."""
        with client.session_transaction() as sess:
            sess["user_id"] = "9999"

        response = client.post(
            f"/toggle_flag/{self.test_sighting.id}",
            data={"flag": "BAD"},
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 400

    def test_update_address_updates_location_fields(self, client, session):
        """Address update endpoint should persist reverse-geocoded location fields."""
        with client.session_transaction() as sess:
            sess["user_id"] = "9999"

        response = client.post(
            f"/update_address/{self.test_sighting.id}",
            data={
                "plz": "14467",
                "ort": "Potsdam",
                "strasse": "Breite Straße 1",
                "kreis": "Potsdam",
                "land": "Brandenburg",
            },
        )
        assert response.status_code == 200
        payload = json.loads(response.data)
        assert payload["success"] is True

        location = session.get(TblFundorte, self.test_location.id)
        assert location.plz == 14467
        assert location.ort == "Potsdam"
        assert location.strasse == "Breite Straße 1"
        assert location.kreis == "Potsdam"
        assert location.land == "Brandenburg"

    def test_toggle_approve_removes_card_when_filter_no_longer_matches(
        self, client, session
    ):
        """Approving in 'offen' filter should delete the card target via HX-Reswap."""
        with client.session_transaction() as sess:
            sess["user_id"] = "9999"

        response = client.post(
            f"/toggle_approve_sighting/{self.test_sighting.id}",
            data={"filter_status": "offen"},
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        assert response.headers.get("HX-Reswap") == "delete"
        assert response.data == b""

        session.refresh(self.test_sighting)
        assert "APPR" in (self.test_sighting.statuses or [])

    def test_export_xlsx_all_data(self, client):
        """Test exporting all data as Excel file."""
        # Set up session
        with client.session_transaction() as sess:
            sess["user_id"] = "9999"

        response = client.get("/admin/export/xlsx/all")
        assert response.status_code == 200
        assert (
            response.content_type
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Verify we got data (Excel files start with PK for zip format)
        assert len(response.data) > 0
        assert response.data[:2] == b"PK"  # Excel files are zip archives

    def test_export_xlsx_approved_only(self, client, session):
        """Test exporting only approved data."""
        # Set up session
        with client.session_transaction() as sess:
            sess["user_id"] = "9999"

        # Approve the sighting
        self.test_sighting.bearb_id = "9999"
        self.test_sighting.dat_bear = datetime.now().date()
        session.commit()

        response = client.get("/admin/export/xlsx/accepted")
        assert response.status_code == 200
        assert (
            response.content_type
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Verify we got data
        assert len(response.data) > 0
        assert response.data[:2] == b"PK"

    def test_alldata_view_access(self, client):
        """Test accessing the alldata view."""
        # Set up session
        with client.session_transaction() as sess:
            sess["user_id"] = "9999"

        response = client.get("/alldata")
        assert response.status_code == 200
        assert b"database" in response.data.lower()

    def test_get_table_data_api(self, client):
        """Test getting table data via API."""
        # Set up session
        with client.session_transaction() as sess:
            sess["user_id"] = "9999"

        # Test getting all_data_view table data
        response = client.get("/admin/get_table_data/all_data_view?page=1&per_page=10")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert "data" in data
        assert "total_items" in data
        assert "columns" in data
        assert len(data["data"]) > 0  # Should have at least our test sighting

    def test_update_cell_valid_table(self, client, session):
        """Test updating a cell in a valid table."""
        # Set up session
        with client.session_transaction() as sess:
            sess["user_id"] = "9999"

        # Update anm_melder field
        response = client.post(
            "/admin/update_cell",
            json={
                "table": "all_data_view",
                "meldungen_id": self.test_sighting.id,
                "column": "anm_melder",
                "value": "Updated comment",
            },
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True

        # Verify in database
        session.refresh(self.test_sighting)
        assert self.test_sighting.anm_melder == "Updated comment"

    def test_update_cell_non_editable_field(self, client):
        """Test that non-editable fields cannot be updated."""
        # Set up session
        with client.session_transaction() as sess:
            sess["user_id"] = "9999"

        # Try to update non-editable field (meldungen_id)
        response = client.post(
            "/admin/update_cell",
            json={
                "table": "all_data_view",
                "meldungen_id": self.test_sighting.id,
                "column": "meldungen_id",
                "value": "999",
            },
        )
        assert response.status_code == 403
        data = json.loads(response.data)
        assert "not editable" in data["error"]

    def test_static_file_serving(self, client):
        """Test serving static files through admin route."""
        # Set up session
        with client.session_transaction() as sess:
            sess["user_id"] = "9999"

        # Test accessing a file (assuming test file exists)
        response = client.get("/test_image.jpg")
        # Should either return the file or 404 if it doesn't exist
        assert response.status_code in [200, 404]

    def test_pagination_on_reviewer_page(self, client, session):
        """Test pagination functionality on reviewer page."""
        # Create multiple sightings for pagination
        for i in range(25):
            location = TblFundorte(
                mtb="3644",
                longitude="13.404954",
                latitude="52.520008",
                ort=f"Test City {i}",
                land="Test State",
                kreis="Test District",
                strasse=f"Test Street {i}",
                plz=10178,
                amt="Test Amt",
                ablage=f"test_image_{i}.jpg",
                beschreibung=self.test_description.id,
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
                anm_melder=f"Test sighting {i}",
                deleted=False,
                bearb_id=None,
            )
            session.add(sighting)

        session.commit()

        # Test first page - need to include required params
        response = client.get(
            "/reviewer/9999?page=1&per_page=10&statusInput=offen&sort_order=id_desc"
        )
        assert response.status_code == 200

        # Test second page - need to include required params
        response = client.get(
            "/reviewer/9999?page=2&per_page=10&statusInput=offen&sort_order=id_desc"
        )
        assert response.status_code == 200

    def test_error_handling_for_invalid_sighting_id(self, client):
        """Test error handling when sighting ID doesn't exist."""
        # Set up session
        with client.session_transaction() as sess:
            sess["user_id"] = "9999"

        # Test with non-existent ID
        response = client.post("/delete_sighting/99999")
        assert response.status_code == 404
