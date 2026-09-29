"""Tests for admin routes including reviewer interface and data management."""

import json
import re
import tempfile
from datetime import date, datetime, timedelta
from io import BytesIO
from smtplib import SMTPServerDisconnected

import openpyxl
import pytest
from bs4 import BeautifulSoup
from sqlalchemy import func, select

from app.database.models import (
    TblFundortBeschreibung,
    TblFundorte,
    TblMeldungen,
    TblMeldungUser,
    TblUsers,
)
from app.extensions import mail
from app.routes.admin import database, export
from app.routes.admin.database import GRID_PAGE_SIZE


def exported_ids(response):
    workbook = openpyxl.load_workbook(BytesIO(response.data), read_only=True)
    try:
        rows = workbook["Daten"].values
        headers = next(rows)
        id_column = headers.index("ID")
        return {row[id_column] for row in rows}
    finally:
        workbook.close()


class TestAdminRoutes:
    """Test suite for admin and reviewer routes."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, app, session):
        """Set up test data for admin tests."""
        self.session = session

        # Look up the seed-data reviewer (user_id='9999', inserted by filldb.py)
        # instead of creating a duplicate that would violate the UNIQUE constraint.
        self.reviewer_user = session.scalar(
            select(TblUsers).where(TblUsers.user_id == "9999")
        )

        # Look up or create regular user (non-reviewer).
        self.regular_user = session.scalar(
            select(TblUsers).where(TblUsers.user_id == "1111")
        )
        if not self.regular_user:
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

        self.test_location = TblFundorte(
            mtb="3644",
            longitude="13.404954",
            latitude="52.520008",
            ort="Test City",
            land="Test State",
            kreis="Test District",
            strasse="Test Street",
            plz="10178",
            amt="Test Amt",
            ablage="test_image.jpg",
            beschreibung=self.test_description.id,
        )
        session.add(self.test_location)
        session.flush()

        self.test_sighting = TblMeldungen(
            dat_fund_von=datetime.now().date() - timedelta(days=7),
            dat_meld=datetime.now().date(),
            fo_zuordnung=self.test_location.id,
            art_m=1,
            art_w=0,
            art_n=0,
            art_o=0,
            anm_melder="Test sighting",
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

        return

    def test_reviewer_page_access_with_valid_reviewer(self, client):
        """Test that reviewers can access the reviewer page."""
        # Follow redirects to handle the automatic redirect to add default params
        response = client.get("/reviewer/9999", follow_redirects=True)
        assert response.status_code == 200
        assert b"Admin Panel" in response.data or b"admin" in response.data.lower()
        # Check that session was set
        with client.session_transaction() as sess:
            assert sess.get("_user_id") == "9999"

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
            assert "_user_id" not in sess

        response = client.get("/reviewer/9999", follow_redirects=True)
        assert response.status_code == 200

        with client.session_transaction() as sess:
            assert sess["_user_id"] == "9999"

    def test_provider_view_preserves_reviewer_session(self, client):
        """Opening provider page should not override active reviewer auth session."""
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

        response = client.get("/report/1111")
        assert response.status_code == 200

        with client.session_transaction() as sess:
            assert sess["_user_id"] == "9999"

    def test_sichtungen_alias_preserves_reviewer_session(self, client):
        """Alias route should also preserve active reviewer auth session."""
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

        response = client.get("/sichtungen/1111")
        assert response.status_code == 200

        with client.session_transaction() as sess:
            assert sess["_user_id"] == "9999"

    def test_provider_view_sets_session_for_non_reviewer_context(self, client):
        """Provider link should still initialize session in non-reviewer context."""
        with client.session_transaction() as sess:
            sess.clear()

        response = client.get("/report/1111")
        assert response.status_code == 200

        with client.session_transaction() as sess:
            assert sess.get("_user_id") == "1111"

    def test_provider_view_melden_button_uses_viewed_user_id(self, client):
        """Provider page CTA should target viewed reporter ID, not active session user."""
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"  # Active reviewer session

        response = client.get("/report/1111")
        assert response.status_code == 200
        assert b"/melden/1111" in response.data

    def test_provider_view_does_not_render_reviewer_nav_links(self, client):
        """Provider page should not expose reviewer/statistics nav links for reporter context."""
        with client.session_transaction() as sess:
            sess.clear()

        response = client.get("/report/1111")
        assert response.status_code == 200
        assert b"/reviewer/1111" not in response.data
        assert b"/statistik" not in response.data

    def test_toggle_approve_still_works_after_opening_provider_page(
        self, client, session
    ):
        """Reviewer should remain authorized for approve actions after provider page visit."""
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

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
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

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
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

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

    def test_an_approval_stands_when_the_mail_server_refuses(
        self, app, client, session, monkeypatch
    ):
        # The reporter has an address, notifications are on, SMTP is down.
        self.test_relation.id_user = self.regular_user.id
        session.commit()
        app.config["REVIEWERMAIL"] = True

        def refuse(message):
            raise SMTPServerDisconnected("Connection unexpectedly closed")

        monkeypatch.setattr(mail, "send", refuse)
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

        response = client.post(
            f"/toggle_approve_sighting/{self.test_sighting.id}",
            data={"filter_status": "all"},
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 200
        session.refresh(self.test_sighting)
        assert self.test_sighting.statuses == ["APPR"]

    def test_toggle_approve_sighting_without_email(self, client, session):
        """Test that approving works even when email sending is disabled."""
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

        # Approve sighting (emails are disabled in test config)
        response = client.post(
            f"/toggle_approve_sighting/{self.test_sighting.id}",
            data={"filter_status": "all"},
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        assert b'id="report-card-' in response.data

        # Verify approval happened
        session.refresh(self.test_sighting)
        assert self.test_sighting.bearb_id == "9999"
        assert self.test_sighting.dat_bear is not None

    def test_delete_sighting(self, client, session):
        """Test soft deleting a sighting."""
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

        # Delete sighting
        response = client.post(
            f"/delete_sighting/{self.test_sighting.id}",
            data={"filter_status": "all"},
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        assert b'id="report-card-' in response.data

        # Verify soft delete in database
        session.refresh(self.test_sighting)
        assert self.test_sighting.is_deleted

    def test_undelete_sighting(self, client, session):
        """Test undeleting a soft-deleted sighting."""
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

        # First delete the sighting
        self.test_sighting.statuses = ["DEL"]
        session.commit()

        # Undelete sighting
        response = client.post(
            f"/undelete_sighting/{self.test_sighting.id}",
            data={"filter_status": "all"},
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        assert b'id="report-card-' in response.data

        # Verify undelete in database
        session.refresh(self.test_sighting)
        assert not self.test_sighting.is_deleted

    def test_change_mantis_count(self, client, session):
        """Test changing mantis count fields."""
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

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

    def test_change_mantis_count_invalid_type(self, client, session):
        """Unknown count types should return 400 and not mutate report data."""
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

        before = (self.test_sighting.art_m, self.test_sighting.bearb_id)
        response = client.post(
            f"/change_mantis_count/{self.test_sighting.id}",
            data={"type": "InvalidType", "new_count": "2"},
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

        session.refresh(self.test_sighting)
        after = (self.test_sighting.art_m, self.test_sighting.bearb_id)
        assert after == before

    def test_change_mantis_count_invalid_value(self, client, session):
        """Non-numeric count values should be rejected with 400."""
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

        original = self.test_sighting.art_m
        response = client.post(
            f"/change_mantis_count/{self.test_sighting.id}",
            data={"type": "Männchen", "new_count": "abc"},
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

        session.refresh(self.test_sighting)
        assert self.test_sighting.art_m == original

    def test_change_mantis_count_negative_value(self, client, session):
        """Negative count values are invalid and should be rejected."""
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

        original = self.test_sighting.art_m
        response = client.post(
            f"/change_mantis_count/{self.test_sighting.id}",
            data={"type": "Männchen", "new_count": "-1"},
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

        session.refresh(self.test_sighting)
        assert self.test_sighting.art_m == original

    def test_change_mantis_count_out_of_range_value(self, client, session):
        """Counts beyond DB integer range should return 400."""
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

        original = self.test_sighting.art_m
        response = client.post(
            f"/change_mantis_count/{self.test_sighting.id}",
            data={"type": "Männchen", "new_count": "2147483648"},
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

        session.refresh(self.test_sighting)
        assert self.test_sighting.art_m == original

    def test_reviewer_page_uses_native_modal_and_fragment_assets(self, client):
        """Reviewer page should load native dialog + HTMX admin modules."""
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

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
            sess["_user_id"] = "9999"

        response = client.get(f"/modal/{self.test_sighting.id}?filter_status=offen")
        assert response.status_code == 200
        assert b'id="tab-content"' in response.data
        assert b"General Information" in response.data
        assert b'id="modal-actions"' in response.data

    def test_modal_general_tab_shows_user_report_count(self, client):
        """General tab should display the reporter's total report count."""
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

        response = client.get(f"/modal/{self.test_sighting.id}?filter_status=offen")
        assert response.status_code == 200
        html = response.data.decode()
        assert "Meldungen" in html
        # Compact "Freigabe" layout renders the count under an "Anzahl Meldungen" label
        assert "Anzahl Meldungen" in html

    def test_modal_location_tab_response_contains_oob_updates(self, client):
        """Location tab endpoint should return tab content plus OOB tab/action updates."""
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

        response = client.get(
            f"/modal/location/{self.test_sighting.id}?filter_status=offen"
        )
        assert response.status_code == 200
        assert b'id="map"' in response.data
        assert b'hx-swap-oob="outerHTML"' in response.data
        assert b'id="modal-actions"' in response.data

    def test_toggle_flag_returns_card_partial(self, client, session):
        """A report still matching the active filter comes back as a card."""
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

        response = client.post(
            f"/toggle_flag/{self.test_sighting.id}",
            data={"flag": "UNKL", "filter_status": "all"},
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        assert b'id="report-card-' in response.data
        # Modal footer is kept in sync out-of-band
        assert b'id="modal-actions"' in response.data

        session.refresh(self.test_sighting)
        assert "UNKL" in (self.test_sighting.statuses or [])

    def test_toggle_flag_removes_card_when_it_leaves_the_filter(self, client, session):
        """Marking a report "Unklar" takes it out of the "offen" bucket.

        The list must drop the card rather than re-render it, so the response
        is an HTMX delete swap — the modal footer still rides along OOB.
        """
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

        response = client.post(
            f"/toggle_flag/{self.test_sighting.id}",
            data={"flag": "UNKL", "filter_status": "offen"},
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 200
        assert response.headers["HX-Reswap"] == "delete"
        assert b'id="report-card-' not in response.data
        assert b'id="modal-actions"' in response.data

        session.refresh(self.test_sighting)
        assert "UNKL" in (self.test_sighting.statuses or [])

    def test_toggle_flag_invalid_value(self, client):
        """Invalid flag values should be rejected."""
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

        response = client.post(
            f"/toggle_flag/{self.test_sighting.id}",
            data={"flag": "BAD"},
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 400

    def test_update_address_updates_location_fields(self, client, session):
        """Address update endpoint should persist reverse-geocoded location fields."""
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

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
        assert location.plz == "14467"
        assert location.ort == "Potsdam"
        assert location.strasse == "Breite Straße 1"
        assert location.kreis == "Potsdam"
        assert location.land == "Brandenburg"

    def test_update_address_rejects_oversized_zip(self, client, session):
        """Oversized ZIP values should return 400 and keep existing ZIP."""
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

        original_plz = self.test_location.plz
        response = client.post(
            f"/update_address/{self.test_sighting.id}",
            data={
                "plz": "9999999999999999999999999",
                "ort": "Potsdam",
                "strasse": "Breite Straße 1",
                "kreis": "Potsdam",
                "land": "Brandenburg",
            },
        )
        assert response.status_code == 400
        payload = json.loads(response.data)
        assert "error" in payload

        location = session.get(TblFundorte, self.test_location.id)
        assert location.plz == original_plz

    def test_toggle_approve_removes_card_when_filter_no_longer_matches(
        self, client, session
    ):
        """Approving in 'offen' filter should delete the card target via HX-Reswap."""
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

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
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

        response = client.get("/admin/export/xlsx/all")
        assert response.status_code == 200
        assert (
            response.content_type
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        assert self.test_sighting.id in exported_ids(response)

    def test_export_xlsx_approved_only(self, client, session):
        """Test exporting only approved data."""
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

        # The legacy reviewer/date columns alone do not approve a report.
        self.test_sighting.statuses = ["APPR"]
        self.test_sighting.bearb_id = "9999"
        self.test_sighting.dat_bear = datetime.now().date()
        session.commit()

        response = client.get("/admin/export/xlsx/accepted")
        assert response.status_code == 200
        assert (
            response.content_type
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        expected = set(
            session.scalars(
                select(TblMeldungen.id).where(TblMeldungen.statuses.contains(["APPR"]))
            )
        )
        assert self.test_sighting.id in expected
        assert exported_ids(response) == expected

    def test_export_xlsx_column_values_match_headers(self, client):
        """Each column must carry the value its header promises.

        The other export tests only check that a zip arrives, so a shifted
        column index would pass them silently while corrupting every export.
        """
        from io import BytesIO

        import openpyxl

        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

        response = client.get("/admin/export/xlsx/all")
        assert response.status_code == 200

        sheet = openpyxl.load_workbook(BytesIO(response.data)).active
        assert sheet is not None
        rows = list(sheet.values)
        headers = list(rows[0])

        row = next(
            r for r in rows[1:] if r[headers.index("ID")] == self.test_sighting.id
        )
        cells = dict(zip(headers, row, strict=True))

        assert cells["Ort"] == "Test City"
        assert cells["Land"] == "Test State"
        assert cells["Kreis"] == "Test District"
        assert cells["Straße"] == "Test Street"
        assert cells["PLZ"] == "10178"
        assert cells["Amt"] == "Test Amt"
        assert cells["MTB"] == "3644"
        assert cells["Längengrad"] == 13.404954
        assert cells["Breitengrad"] == 52.520008
        assert cells["Männchen"] == 1
        assert cells["Anmerkung Melder"] == "Test sighting"
        # xlsxwriter stores "" as an empty cell, which reads back as None
        assert cells["Bearbeiter"] is None  # not approved yet

    def test_export_keeps_a_reporter_remark_that_looks_like_a_formula_as_text(
        self, client, session
    ):
        # A public reporter types a formula into the remark field.
        self.test_sighting.anm_melder = '=HYPERLINK("https://example.com","Foto")'
        session.commit()
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

        response = client.get("/admin/export/xlsx/all")

        sheet = openpyxl.load_workbook(BytesIO(response.data))["Daten"]
        headers = [cell.value for cell in sheet[1]]
        row = next(
            r for r in sheet.iter_rows(min_row=2) if r[0].value == self.test_sighting.id
        )
        remark = row[headers.index("Anmerkung Melder")]
        assert remark.data_type == "s"
        assert remark.value == '=HYPERLINK("https://example.com","Foto")'

    def test_a_large_export_leaves_no_file_behind(self, client, monkeypatch, tmp_path):
        # Every export counts as large, and temp files land in tmp_path.
        monkeypatch.setattr(export, "LARGE_EXPORT_THRESHOLD", 0)
        monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

        response = client.get("/admin/export/xlsx/all")
        assert self.test_sighting.id in exported_ids(response)
        response.close()

        assert list(tmp_path.iterdir()) == []

    def test_export_xlsx_searched(self, client):
        """Test exporting searched data with the shared reviewer filter args."""
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

        response = client.get(
            "/admin/export/xlsx/searched"
            "?statusInput=offen"
            "&q=Test"
            "&search_type=full_text"
            "&dateFrom=01.01.2024"
            "&dateTo=31.12.2026"
            "&dateType=fund"
        )
        assert response.status_code == 200
        assert (
            response.content_type
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        assert exported_ids(response) == {self.test_sighting.id}

    def test_export_of_an_unknown_selection_is_not_found(self, client):
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

        response = client.get("/admin/export/xlsx/geloescht")
        assert response.status_code == 404

    def test_alldata_view_access(self, client):
        """Test accessing the alldata view."""
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

        response = client.get("/alldata")
        assert response.status_code == 200
        assert b"database" in response.data.lower()

    def grid(self, client, **args):
        """The grid fragment htmx loads: page 1 is the table, later pages only rows."""
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"
        return client.get("/alldata", query_string=args, headers={"HX-Request": "true"})

    @staticmethod
    def grid_ids(response):
        return [int(id_) for id_ in re.findall(r'id="cell-(\d+)-tiere"', response.text)]

    def test_grid_fragment_lists_reports_with_editable_cells(self, client):
        response = self.grid(client)
        assert response.status_code == 200
        soup = BeautifulSoup(response.data, "html.parser")

        assert soup.find("html") is None
        assert self.test_sighting.id in self.grid_ids(response)
        assert soup.select_one(f"#cell-{self.test_sighting.id}-strasse")
        assert not soup.select("[id$=-statuses], [id$=-beschreibung]")

    def test_grid_full_text_search_filters_rows(self, client):
        response = self.grid(client, q="Test sighting", search_type="full_text")
        assert self.grid_ids(response) == [self.test_sighting.id]

    def test_grid_invalid_id_search_returns_no_rows(self, client):
        response = self.grid(client, q="not-an-int", search_type="id")
        assert response.status_code == 200
        assert self.grid_ids(response) == []

    def test_grid_sorts_by_the_requested_column(self, client):
        sort_ids = self.grid_ids(self.grid(client, sort="meldungen_id", dir="desc"))
        assert sort_ids == sorted(sort_ids, reverse=True)

    def test_grid_loads_the_rest_on_the_next_page(self, client, session):
        for _ in range(GRID_PAGE_SIZE + 2):
            report = TblMeldungen(
                dat_fund_von=date.today(),
                dat_meld=date.today(),
                fo_zuordnung=self.test_location.id,
            )
            session.add(report)
            session.flush()
            session.add(
                TblMeldungUser(id_meldung=report.id, id_user=self.reviewer_user.id)
            )
        session.commit()
        total = session.scalar(select(func.count(TblMeldungen.id)))

        first = self.grid(client)
        second = self.grid(client, page=2)

        assert len(self.grid_ids(first)) == GRID_PAGE_SIZE
        assert 'hx-trigger="intersect once"' in first.text
        assert "page=2" in first.text
        assert len(self.grid_ids(second)) == total - GRID_PAGE_SIZE
        assert "hx-trigger" not in second.text
        assert "<table" not in second.text

    @pytest.mark.parametrize("sort_column", ["fo_quelle", "land", "tiere"])
    def test_paging_the_grid_by_a_shared_value_shows_every_report_once(
        self, client, session, monkeypatch, sort_column
    ):
        # Sorted by a column many reports share, one row per page.
        monkeypatch.setattr(database, "GRID_PAGE_SIZE", 1)
        all_ids = list(session.scalars(select(TblMeldungen.id)))

        seen = []
        for page in range(1, len(all_ids) + 1):
            seen += self.grid_ids(self.grid(client, page=page, sort=sort_column))

        assert sorted(seen) == sorted(all_ids)

    def post_cell(self, client, report_id, column, value):
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"
        return client.post(
            f"/admin/cell/{report_id}/{column}",
            data={"value": value},
            headers={"HX-Request": "true"},
        )

    def test_cell_editor_offers_the_stored_value(self, client):
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

        response = client.get(f"/admin/cell/{self.test_sighting.id}/strasse")
        assert response.status_code == 200
        assert 'value="Test Street"' in response.text
        assert (
            client.get(f"/admin/cell/{self.test_sighting.id}/ablage").status_code == 403
        )

    def test_update_cell_valid_field(self, client, session):
        """Test updating a field exposed by the superuser table."""
        response = self.post_cell(
            client, self.test_sighting.id, "anm_melder", "Updated comment"
        )
        assert response.status_code == 200
        assert response.headers["HX-Retarget"] == (
            f"#cell-{self.test_sighting.id}-anm_melder"
        )
        assert "Updated comment" in response.text
        # A fresh, closed editor dialog replaces the open one.
        assert '<dialog id="editModal"' in response.text

        # Verify in database
        session.refresh(self.test_sighting)
        assert self.test_sighting.anm_melder == "Updated comment"

    def test_update_cell_is_immediately_visible(self, client, session):
        """The table view reflects the committed edit without a refresh."""
        response = self.post_cell(
            client, self.test_sighting.id, "strasse", "Neue Straße 7"
        )

        assert response.status_code == 200
        session.expire_all()
        assert (
            session.get(TblFundorte, self.test_location.id).strasse == "Neue Straße 7"
        )
        from app.database.alldata import TblAllData

        assert (
            session.scalar(
                select(TblAllData.strasse).where(
                    TblAllData.meldungen_id == self.test_sighting.id
                )
            )
            == "Neue Straße 7"
        )

    @pytest.mark.parametrize(
        "column, value, stored",
        [
            ("dat_meld", "2024-05-06", date(2024, 5, 6)),
            ("plz", "", None),
            ("plz", "14467", "14467"),
            ("latitude", "52,4", 52.4),
        ],
    )
    def test_update_cell_stores_normalized_value(
        self, client, session, column, value, stored
    ):
        response = self.post_cell(client, self.test_sighting.id, column, value)
        assert response.status_code == 200
        session.expire_all()
        report = session.get(TblMeldungen, self.test_sighting.id)
        owner = report if column.startswith("dat_") else report.fundort
        assert getattr(owner, column) == stored

    def test_update_cell_recalculates_mtb_for_new_coordinates(self, client, session):
        self.post_cell(client, self.test_sighting.id, "latitude", "52,4")
        session.expire_all()
        assert session.get(TblFundorte, self.test_location.id).mtb != "3644"

    @pytest.mark.parametrize(
        "column, value, message",
        [
            ("plz", "not-a-zip", "Invalid ZIP code"),
            ("latitude", "abc", None),
        ],
    )
    def test_update_cell_rejects_invalid_location_value(
        self, client, session, column, value, message
    ):
        original = getattr(self.test_location, column)
        response = self.post_cell(client, self.test_sighting.id, column, value)
        assert response.status_code == 200
        assert 'role="alert"' in response.text
        assert "HX-Retarget" not in response.headers
        if message:
            assert message in response.text
        session.expire_all()
        assert getattr(session.get(TblFundorte, self.test_location.id), column) == (
            original
        )

    def test_update_cell_updates_the_reporter(self, client, session):
        response = self.post_cell(
            client, self.test_sighting.id, "user_name", "Neuer Name"
        )
        assert response.status_code == 200
        session.expire_all()
        reporter = session.get(TblMeldungen, self.test_sighting.id).reporter_link
        assert reporter.reporter.user_name == "Neuer Name"

    def test_update_cell_unknown_report_is_404(self, client):
        assert self.post_cell(client, 999999, "tiere", "3").status_code == 404

    @pytest.mark.parametrize(
        "column, value",
        [
            ("meldungen_id", "999"),
            # Internal review state must not be reachable through the cell
            # editor — these used to bypass status guards entirely.
            ("deleted", "true"),
            ("statuses", "APPR"),
            ("ablage", "/etc/passwd"),
            ("bearb_id", "9999"),
            ("fo_zuordnung", "1"),
            # This is a shared lookup label. Editing it here would rename the
            # category for every report that references the same row.
            ("beschreibung", "Neuer Fundorttyp"),
        ],
    )
    def test_update_cell_non_editable_field(self, client, column, value):
        """Test that non-editable fields cannot be updated."""
        response = self.post_cell(client, self.test_sighting.id, column, value)
        assert response.status_code == 403

    @pytest.mark.parametrize("column", ["id", "not_a_column"])
    def test_update_cell_rejects_columns_the_view_does_not_expose(self, client, column):
        """`column` is attacker-controlled, so only view columns are accepted."""
        response = self.post_cell(client, self.test_sighting.id, column, "1")
        assert response.status_code == 403

    def test_update_cell_rejects_a_non_integer_count(self, client, session):
        original = self.test_sighting.tiere
        response = self.post_cell(client, self.test_sighting.id, "tiere", "many")
        assert response.status_code == 200
        assert "whole number" in response.text
        session.expire_all()
        assert session.get(TblMeldungen, self.test_sighting.id).tiere == original

    def test_change_mantis_meta_plz_non_numeric_returns_400(self, client):
        """plz is CHECK-constrained to 5 digits — non-numeric input must yield 400, not 500."""
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

        response = client.post(
            f"/change_mantis_meta_data/{self.test_sighting.id}",
            data={"type": "plz", "new_data": "not-a-zip"},
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Invalid ZIP" in data["error"]

    def test_static_file_serving(self, app, client, tmp_path, monkeypatch):
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"
        monkeypatch.setitem(app.config, "UPLOAD_FOLDER", str(tmp_path))
        (tmp_path / "test_image.jpg").write_bytes(b"test photo bytes")
        response = client.get("/admin/images/test_image.jpg")
        assert response.status_code == 200
        assert response.data == b"test photo bytes"
        assert client.get("/admin/images/missing.jpg").status_code == 404

    @pytest.mark.parametrize("extra_query", [{}, {"endpoint": "x"}])
    def test_pagination_on_reviewer_page(self, client, session, extra_query):
        ids = []
        for _ in range(25):
            sighting = TblMeldungen(
                dat_fund_von=datetime.now().date() - timedelta(days=1),
                dat_meld=datetime.now().date(),
                fundort=self.test_location,
                anm_melder="Paginationkontrolle",
                statuses=["OPEN"],
            )
            session.add(sighting)
            session.flush()
            session.add(
                TblMeldungUser(id_meldung=sighting.id, id_user=self.reviewer_user.id)
            )
            ids.append(sighting.id)
        session.commit()

        for page, expected in (
            (1, sorted(ids, reverse=True)[:10]),
            (2, sorted(ids, reverse=True)[10:20]),
            (3, sorted(ids, reverse=True)[20:]),
        ):
            response = client.get(
                "/reviewer/9999",
                query_string={
                    "page": page,
                    "per_page": 10,
                    "statusInput": "offen",
                    "sort_order": "id_desc",
                    "q": "Paginationkontrolle",
                    "search_type": "full_text",
                    **extra_query,
                },
            )
            assert response.status_code == 200
            cards = BeautifulSoup(response.data, "html.parser").select(
                '[id^="report-card-"]'
            )
            assert [card["id"] for card in cards] == [
                f"report-card-{id}" for id in expected
            ]

    def test_error_handling_for_invalid_sighting_id(self, client, session):
        """Test error handling when sighting ID doesn't exist."""
        with client.session_transaction() as sess:
            sess["_user_id"] = "9999"

        # Test with non-existent ID
        missing_id = (session.scalar(select(func.max(TblMeldungen.id))) or 0) + 1
        response = client.post(f"/delete_sighting/{missing_id}")
        assert response.status_code == 404
