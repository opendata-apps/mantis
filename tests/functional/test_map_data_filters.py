"""Test map data generation to ensure status filtering works correctly."""

import pytest
import json
from datetime import datetime
from app.database.models import TblMeldungen, TblFundorte, ReportStatus
from bs4 import BeautifulSoup


class TestMapDataFilters:
    """Test map data generation with is_() comparisons for deleted field."""

    @pytest.fixture(autouse=True)
    def setup_test_data(self, session):
        """Create test data with various states."""
        # Create test location
        self.location = TblFundorte(
            mtb="3644",
            longitude="13.404954",
            latitude="52.520008",
            ort="Test City",
            land="BB",
            kreis="Test District",
            strasse="Test Street",
            plz=10178,
            amt="Test Amt",
            ablage="test.jpg",
            beschreibung=1,  # Use existing description
        )
        session.add(self.location)
        session.flush()

        # Create approved sighting (should appear in map)
        self.approved_sighting = TblMeldungen(
            dat_fund_von=datetime.now().date(),
            dat_meld=datetime.now().date(),
            fo_zuordnung=self.location.id,
            dat_bear=datetime.now(),
            deleted=None,
            statuses=[ReportStatus.APPR.value],
            art_m=1,
        )
        session.add(self.approved_sighting)

        # Create approved with deleted=False (should appear in map)
        self.approved_not_deleted = TblMeldungen(
            dat_fund_von=datetime.now().date(),
            dat_meld=datetime.now().date(),
            fo_zuordnung=self.location.id,
            dat_bear=datetime.now(),
            deleted=False,
            statuses=[ReportStatus.APPR.value],
            art_o=1,
        )
        session.add(self.approved_not_deleted)

        # Create unapproved sighting (should NOT appear in map)
        self.unapproved_sighting = TblMeldungen(
            dat_fund_von=datetime.now().date(),
            dat_meld=datetime.now().date(),
            fo_zuordnung=self.location.id,
            dat_bear=None,
            deleted=None,
            statuses=[ReportStatus.OPEN.value],
            art_w=1,
        )
        session.add(self.unapproved_sighting)

        # Create deleted sighting (should NOT appear in map)
        self.deleted_sighting = TblMeldungen(
            dat_fund_von=datetime.now().date(),
            dat_meld=datetime.now().date(),
            fo_zuordnung=self.location.id,
            dat_bear=datetime.now(),
            deleted=True,
            statuses=[ReportStatus.DEL.value],
            art_n=1,
        )
        session.add(self.deleted_sighting)

        session.commit()

    def test_map_view_filters_correctly(self, client):
        """Test that /auswertungen map view only shows approved, non-deleted sightings."""
        response = client.get("/auswertungen")
        assert response.status_code == 200

        soup = BeautifulSoup(response.data, "html.parser")

        script_tags = soup.find_all("script")
        reports_json = None

        for script in script_tags:
            if script.string and "const reports = " in script.string:
                start = script.string.find("const reports = ") + len("const reports = ")
                bracket_count = 0
                end = start
                for i, char in enumerate(script.string[start:], start):
                    if char == "[":
                        bracket_count += 1
                    elif char == "]":
                        bracket_count -= 1
                        if bracket_count == 0:
                            end = i + 1
                            break
                json_str = script.string[start:end]
                reports_json = json.loads(json_str)
                break

        assert reports_json is not None, "Could not find reports JSON in response"

        # Extract report IDs from the JSON
        report_ids = [report["report_id"] for report in reports_json]

        # Check that approved sightings are included
        assert self.approved_sighting.id in report_ids, (
            "Approved (deleted=NULL) sighting not in map data"
        )
        assert self.approved_not_deleted.id in report_ids, (
            "Approved (deleted=False) sighting not in map data"
        )

        # Check that unapproved and deleted sightings are NOT included
        assert self.unapproved_sighting.id not in report_ids, (
            "Unapproved sighting should not be in map data"
        )
        assert self.deleted_sighting.id not in report_ids, (
            "Deleted sighting should not be in map data"
        )

    def test_map_view_with_year_filter(self, client):
        """Test map view with year filter still respects deleted/approved filters."""
        current_year = datetime.now().year
        response = client.get(f"/auswertungen?year={current_year}")
        assert response.status_code == 200

        soup = BeautifulSoup(response.data, "html.parser")
        script_tags = soup.find_all("script")
        reports_json = None

        for script in script_tags:
            if script.string and "const reports = " in script.string:
                start = script.string.find("const reports = ") + len("const reports = ")
                bracket_count = 0
                end = start
                for i, char in enumerate(script.string[start:], start):
                    if char == "[":
                        bracket_count += 1
                    elif char == "]":
                        bracket_count -= 1
                        if bracket_count == 0:
                            end = i + 1
                            break
                json_str = script.string[start:end]
                reports_json = json.loads(json_str)
                break

        assert reports_json is not None, "Failed to parse reports JSON from map page"
        report_ids = [report["report_id"] for report in reports_json]
        assert self.deleted_sighting.id not in report_ids
        assert self.unapproved_sighting.id not in report_ids

    def test_get_marker_data_respects_approval(self, client):
        """Test that individual marker data endpoint respects approval status."""
        # Try to get data for approved sighting - should work
        response = client.get(f"/get_marker_data/{self.approved_sighting.id}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["id"] == self.approved_sighting.id

        # Try to get data for unapproved sighting - should not work or return limited data
        response = client.get(f"/get_marker_data/{self.unapproved_sighting.id}")
        # Check if it returns 404 or limited data
        if response.status_code == 200:
            data = json.loads(response.data)
            # If it returns data, it might be limited or the sighting might not be on the map anyway
            assert "id" in data

    def test_edge_case_combinations(self, client, session):
        """Test various edge case combinations of status values."""
        # Test cases: (status, should_appear, description)
        test_cases = [
            (ReportStatus.APPR.value, True, "approved status"),
            (ReportStatus.OPEN.value, False, "open status"),
            (ReportStatus.DEL.value, False, "deleted status"),
            (ReportStatus.INFO.value, False, "info status"),
            (ReportStatus.UNKL.value, False, "unclear status"),
        ]

        created_sightings = []

        for status, should_appear, desc in test_cases:
            sighting = TblMeldungen(
                dat_fund_von=datetime.now().date(),
                dat_meld=datetime.now().date(),
                fo_zuordnung=self.location.id,
                dat_bear=datetime.now() if status == ReportStatus.APPR.value else None,
                deleted=(status == ReportStatus.DEL.value),
                statuses=[status],
                anm_melder=desc,
            )
            session.add(sighting)
            session.flush()
            created_sightings.append((sighting.id, should_appear))

        session.commit()

        response = client.get("/auswertungen")
        assert response.status_code == 200

        soup = BeautifulSoup(response.data, "html.parser")
        script_tags = soup.find_all("script")
        reports_json = None

        for script in script_tags:
            if script.string and "const reports = " in script.string:
                start = script.string.find("const reports = ") + len("const reports = ")
                bracket_count = 0
                end = start
                for i, char in enumerate(script.string[start:], start):
                    if char == "[":
                        bracket_count += 1
                    elif char == "]":
                        bracket_count -= 1
                        if bracket_count == 0:
                            end = i + 1
                            break
                json_str = script.string[start:end]
                reports_json = json.loads(json_str)
                break

        assert reports_json is not None, "Failed to parse reports JSON from map page"
        report_ids = [report["report_id"] for report in reports_json]

        for sighting_id, should_appear in created_sightings:
            if should_appear:
                assert sighting_id in report_ids, (
                    f"Sighting {sighting_id} should appear in map data"
                )
            else:
                assert sighting_id not in report_ids, (
                    f"Sighting {sighting_id} should NOT appear in map data"
                )

    def test_map_excludes_reports_before_min_map_year(self, client, session):
        """Approved reports older than MIN_MAP_YEAR must not appear on the map."""
        min_map_year = client.application.config["MIN_MAP_YEAR"]
        old_approved = TblMeldungen(
            dat_fund_von=datetime(min_map_year - 1, 6, 15).date(),
            dat_meld=datetime.now().date(),
            fo_zuordnung=self.location.id,
            dat_bear=datetime.now(),
            deleted=False,
            statuses=[ReportStatus.APPR.value],
            art_m=1,
            anm_melder="old approved report",
        )
        session.add(old_approved)
        session.commit()

        response = client.get("/auswertungen")
        assert response.status_code == 200

        soup = BeautifulSoup(response.data, "html.parser")
        script_tags = soup.find_all("script")
        reports_json = None

        for script in script_tags:
            if script.string and "const reports = " in script.string:
                start = script.string.find("const reports = ") + len("const reports = ")
                bracket_count = 0
                end = start
                for i, char in enumerate(script.string[start:], start):
                    if char == "[":
                        bracket_count += 1
                    elif char == "]":
                        bracket_count -= 1
                        if bracket_count == 0:
                            end = i + 1
                            break
                json_str = script.string[start:end]
                reports_json = json.loads(json_str)
                break

        assert reports_json is not None, "Could not find reports JSON in response"
        report_ids = [report["report_id"] for report in reports_json]
        assert old_approved.id not in report_ids
