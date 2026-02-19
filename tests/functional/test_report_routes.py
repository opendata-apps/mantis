"""HTTP-level tests for all report routes in app/routes/report.py.

Design principles:
- No conditional assertions — every test makes a clear claim and fails loudly
- Tests hit actual Flask routes via the test client
- Only mock file I/O (_process_uploaded_image); test everything else for real
- HTMX endpoints tested with and without HX-Request header
"""

import io
import datetime
from unittest.mock import patch

import pytest
from PIL import Image
from sqlalchemy import select, func
from werkzeug.datastructures import MultiDict
from werkzeug.exceptions import BadRequest, Forbidden

from app.database.models import (
    TblFundorte,
    TblMeldungen,
    TblMeldungUser,
    TblUsers,
    TblUserFeedback,
)
from app.database.feedback_type import FeedbackSource


# ---------------------------------------------------------------------------
# Shared helpers and fixtures
# ---------------------------------------------------------------------------

def _create_test_image(fmt="jpeg", name="test.jpg"):
    """Create a small in-memory image for upload tests."""
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), color="green").save(buf, fmt)
    buf.name = name
    buf.seek(0)
    return buf


def _htmx_headers():
    return {"HX-Request": "true"}


@pytest.fixture
def valid_form_data():
    """Minimal valid form data for a full report submission."""
    sighting_date = (datetime.date.today() - datetime.timedelta(days=3)).strftime(
        "%Y-%m-%d"
    )
    return {
        "report_first_name": "Anna",
        "report_last_name": "Testerin",
        "email": "anna@example.com",
        "identical_finder_reporter": "true",
        "finder_first_name": "",
        "finder_last_name": "",
        "feedback_source": "",
        "feedback_detail": "",
        "sighting_date": sighting_date,
        "latitude": "52.520008",
        "longitude": "13.404954",
        "fund_city": "Berlin",
        "fund_state": "Berlin",
        "fund_district": "Mitte",
        "fund_street": "Alexanderplatz 1",
        "fund_zip_code": "10178",
        "gender": "Männlich",
        "location_description": "2",
        "description": "Auf einer Pflanze entdeckt",
        "honeypot": "",
    }


# ============================================================================
# A. HTMX guard — all 5 HTMX endpoints reject non-HTMX requests
# ============================================================================

HTMX_ENDPOINTS = [
    "/melden/validate-step",
    "/melden/toggle-finder",
    "/melden/feedback-detail",
    "/melden/review",
    "/melden/char-count",
]


class TestHtmxGuard:
    """All HTMX-only endpoints must abort(400) without HX-Request header.

    Note: Flask with TESTING=True propagates exceptions from abort() since
    there is no registered error handler for 400. We verify the correct
    exception type is raised.
    """

    @pytest.mark.parametrize("endpoint", HTMX_ENDPOINTS)
    def test_rejects_non_htmx_request(self, client, endpoint):
        with pytest.raises(BadRequest):
            client.post(endpoint, data={"step": "1"})


# ============================================================================
# B. /melden/validate-step  (HTMX step validation)
# ============================================================================

class TestValidateStepPartial:
    """HTMX endpoint that validates individual form steps."""

    def test_step1_valid(self, client):
        response = client.post(
            "/melden/validate-step",
            headers=_htmx_headers(),
            data={
                "step": "1",
                "gender": "Männlich",
                "location_description": "2",
                "description": "Kurze Beschreibung",
            },
        )
        assert response.status_code == 200
        assert "stepValid" in response.headers.get("HX-Trigger", "")

    def test_step1_missing_gender(self, client):
        response = client.post(
            "/melden/validate-step",
            headers=_htmx_headers(),
            data={"step": "1", "gender": "", "location_description": "2"},
        )
        assert response.status_code == 200
        assert "stepValid" not in response.headers.get("HX-Trigger", "")

    def test_step2_missing_coordinates(self, client):
        response = client.post(
            "/melden/validate-step",
            headers=_htmx_headers(),
            data={
                "step": "2",
                "sighting_date": (
                    datetime.date.today() - datetime.timedelta(days=1)
                ).strftime("%Y-%m-%d"),
                "fund_city": "Berlin",
                "fund_state": "Berlin",
                "latitude": "",
                "longitude": "",
            },
        )
        assert response.status_code == 200
        # Should contain coordinate error, no stepValid trigger
        assert "stepValid" not in response.headers.get("HX-Trigger", "")

    def test_step2_invalid_coordinates(self, client):
        response = client.post(
            "/melden/validate-step",
            headers=_htmx_headers(),
            data={
                "step": "2",
                "sighting_date": (
                    datetime.date.today() - datetime.timedelta(days=1)
                ).strftime("%Y-%m-%d"),
                "fund_city": "Berlin",
                "fund_state": "Berlin",
                "latitude": "999",
                "longitude": "999",
            },
        )
        assert response.status_code == 200
        assert "stepValid" not in response.headers.get("HX-Trigger", "")

    def test_step3_finder_cross_validation(self, client):
        """First name without last name → error."""
        response = client.post(
            "/melden/validate-step",
            headers=_htmx_headers(),
            data={
                "step": "3",
                "report_first_name": "Anna",
                "report_last_name": "Test",
                "email": "",
                "identical_finder_reporter": "",
                "finder_first_name": "Max",
                "finder_last_name": "",
                "feedback_source": "",
            },
        )
        assert response.status_code == 200
        assert "stepValid" not in response.headers.get("HX-Trigger", "")

    def test_step4_always_valid(self, client):
        """Review step has no fields to validate."""
        response = client.post(
            "/melden/validate-step",
            headers=_htmx_headers(),
            data={"step": "4"},
        )
        assert response.status_code == 200
        assert "stepValid" in response.headers.get("HX-Trigger", "")


# ============================================================================
# C. /melden/toggle-finder
# ============================================================================

class TestToggleFinder:

    def test_identical_true_hides_fields(self, client):
        response = client.post(
            "/melden/toggle-finder",
            headers=_htmx_headers(),
            data={"identical_finder_reporter": "true"},
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "hidden" in html or "display: none" in html or "display:none" in html

    def test_not_identical_shows_fields(self, client):
        response = client.post(
            "/melden/toggle-finder",
            headers=_htmx_headers(),
            data={"identical_finder_reporter": "false"},
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "finder_first_name" in html

    def test_missing_param_shows_fields(self, client):
        response = client.post(
            "/melden/toggle-finder",
            headers=_htmx_headers(),
            data={},
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "finder_first_name" in html


# ============================================================================
# E. /melden/feedback-detail
# ============================================================================

class TestFeedbackDetail:

    def test_known_source_shows_detail(self, client):
        response = client.post(
            "/melden/feedback-detail",
            headers=_htmx_headers(),
            data={"feedback_source": "EVENT"},
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "Veranstaltung" in html

    def test_empty_source_hides_detail(self, client):
        response = client.post(
            "/melden/feedback-detail",
            headers=_htmx_headers(),
            data={"feedback_source": ""},
        )
        assert response.status_code == 200
        html = response.data.decode()
        # Should not show a placeholder for an empty source
        assert "Veranstaltung" not in html

    def test_invalid_source_hides_detail(self, client):
        response = client.post(
            "/melden/feedback-detail",
            headers=_htmx_headers(),
            data={"feedback_source": "INVALID_SOURCE"},
        )
        assert response.status_code == 200
        html = response.data.decode()
        # No known placeholder → hidden
        assert "Veranstaltung" not in html


# ============================================================================
# F. /melden/review
# ============================================================================

class TestReviewStep:

    def test_full_review_data(self, client, valid_form_data):
        response = client.post(
            "/melden/review",
            headers=_htmx_headers(),
            data=valid_form_data,
        )
        assert response.status_code == 200
        html = response.data.decode()
        # Date should be reformatted to DD.MM.YYYY
        date_parts = valid_form_data["sighting_date"].split("-")
        expected_date = f"{date_parts[2]}.{date_parts[1]}.{date_parts[0]}"
        assert expected_date in html
        # Coordinates formatted with 6 decimals
        assert "52.520008" in html
        assert "13.404954" in html
        # Gender display text
        assert "Männlich" in html
        # Reporter name
        assert "Anna" in html
        assert "Testerin" in html

    def test_review_with_different_finder(self, client, valid_form_data):
        data = valid_form_data.copy()
        data["identical_finder_reporter"] = ""
        data["finder_first_name"] = "Max"
        data["finder_last_name"] = "Finder"
        response = client.post(
            "/melden/review",
            headers=_htmx_headers(),
            data=data,
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "Max Finder" in html


# ============================================================================
# G. /melden/char-count
# ============================================================================

class TestCharCount:

    def test_short_text(self, client):
        response = client.post(
            "/melden/char-count",
            headers=_htmx_headers(),
            data={"description": "x" * 100},
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "400" in html

    def test_exact_limit(self, client):
        response = client.post(
            "/melden/char-count",
            headers=_htmx_headers(),
            data={"description": "x" * 500},
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "0" in html

    def test_over_limit(self, client):
        response = client.post(
            "/melden/char-count",
            headers=_htmx_headers(),
            data={"description": "x" * 510},
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "-10" in html

    def test_empty(self, client):
        response = client.post(
            "/melden/char-count",
            headers=_htmx_headers(),
            data={"description": ""},
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "500" in html


# ============================================================================
# H. /melden GET
# ============================================================================

class TestMeldenGet:

    def test_renders_form(self, client):
        response = client.get("/melden")
        assert response.status_code == 200
        html = response.data.decode()
        assert 'name="gender"' in html
        assert 'name="sighting_date"' in html
        assert 'name="report_first_name"' in html


# ============================================================================
# I. /success route
# ============================================================================

class TestSuccessRoute:

    def test_without_session_flag(self, client):
        response = client.get("/success")
        assert response.status_code == 200

    def test_with_session_flag(self, client):
        # Set session data
        with client.session_transaction() as sess:
            sess["report_submission_successful"] = True
            sess["last_submission_reporter_id"] = "abc123"
            sess["submission_had_email"] = True

        response = client.get("/success")
        assert response.status_code == 200
        html = response.data.decode()
        assert "abc123" in html

        # Session should be cleared after
        with client.session_transaction() as sess:
            assert "report_submission_successful" not in sess
            assert "last_submission_reporter_id" not in sess


# ============================================================================
# J. /melden POST — successful submission (mock image only)
# ============================================================================

class TestMeldenPostSuccess:

    @patch("app.routes.report._process_uploaded_image")
    def test_successful_submission(
        self, mock_process_image, client, valid_form_data, session
    ):
        mock_process_image.return_value = "2025/2025-01-01/test.webp"

        pre_counts = {
            "meldungen": session.scalar(
                select(func.count()).select_from(TblMeldungen)
            ),
            "fundorte": session.scalar(
                select(func.count()).select_from(TblFundorte)
            ),
            "users": session.scalar(select(func.count()).select_from(TblUsers)),
            "links": session.scalar(
                select(func.count()).select_from(TblMeldungUser)
            ),
        }

        response = client.post(
            "/melden",
            data={**valid_form_data, "photo": _create_test_image()},
            content_type="multipart/form-data",
        )

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data["success"] is True
        assert "redirect_url" in json_data

        mock_process_image.assert_called_once()

        # Verify DB records created
        post_meldungen = session.scalar(
            select(func.count()).select_from(TblMeldungen)
        )
        post_fundorte = session.scalar(
            select(func.count()).select_from(TblFundorte)
        )
        post_users = session.scalar(select(func.count()).select_from(TblUsers))
        post_links = session.scalar(
            select(func.count()).select_from(TblMeldungUser)
        )

        assert post_meldungen == pre_counts["meldungen"] + 1
        assert post_fundorte == pre_counts["fundorte"] + 1
        assert post_users == pre_counts["users"] + 1
        assert post_links == pre_counts["links"] + 1

    @patch("app.routes.report._process_uploaded_image")
    def test_gender_fields_in_db(
        self, mock_process_image, client, valid_form_data, session
    ):
        """Verify the actual _set_gender_fields mapping reaches the DB."""
        mock_process_image.return_value = "2025/2025-01-01/test.webp"
        data = valid_form_data.copy()
        data["gender"] = "Weiblich"
        # Unique description to avoid collision with other tests
        data["description"] = "Gender-Test: Weiblich marker"

        response = client.post(
            "/melden",
            data={**data, "photo": _create_test_image()},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data["success"] is True

        # Find the newly created sighting by unique description
        sighting = session.scalar(
            select(TblMeldungen).where(
                TblMeldungen.anm_melder == data["description"]
            )
        )
        assert sighting is not None
        assert sighting.art_w == 1
        assert sighting.art_m == 0
        assert sighting.art_n == 0
        assert sighting.art_o == 0

    @patch("app.routes.report._process_uploaded_image")
    def test_session_data_set(
        self, mock_process_image, client, valid_form_data, session
    ):
        """After successful submission, session contains redirect data."""
        mock_process_image.return_value = "2025/2025-01-01/test.webp"

        response = client.post(
            "/melden",
            data={**valid_form_data, "photo": _create_test_image()},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200

        with client.session_transaction() as sess:
            assert sess.get("report_submission_successful") is True
            assert sess.get("last_submission_reporter_id") is not None
            assert "submission_had_email" in sess


# ============================================================================
# K. /melden POST — validation failures
# ============================================================================

class TestMeldenPostValidation:

    def test_missing_photo(self, client, valid_form_data):
        response = client.post(
            "/melden",
            data=valid_form_data,  # no photo
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "Ein Foto ist erforderlich" in html

    def test_future_date(self, client, valid_form_data):
        data = valid_form_data.copy()
        data["sighting_date"] = (
            datetime.date.today() + datetime.timedelta(days=10)
        ).strftime("%Y-%m-%d")
        response = client.post(
            "/melden",
            data={**data, "photo": _create_test_image()},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "Zukunft" in html

    def test_invalid_email(self, client, valid_form_data):
        data = valid_form_data.copy()
        data["email"] = "not-an-email"
        response = client.post(
            "/melden",
            data={**data, "photo": _create_test_image()},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        html = response.data.decode()
        assert "E-Mail" in html

    def test_honeypot_filled(self, client, valid_form_data):
        data = valid_form_data.copy()
        data["honeypot"] = "x"
        response = client.post(
            "/melden",
            data={**data, "photo": _create_test_image()},
            content_type="multipart/form-data",
        )
        assert response.status_code == 403


# ============================================================================
# K2. /melden POST — additional coverage for submission branches
# ============================================================================

class TestMeldenPostBranches:
    """Cover additional paths: finder creation, feedback, location_description."""

    @patch("app.routes.report._process_uploaded_image")
    def test_submission_with_separate_finder(
        self, mock_process_image, client, valid_form_data, session
    ):
        """When finder ≠ reporter, a separate TblUsers(role=2) is created."""
        mock_process_image.return_value = "2025/2025-01-01/test.webp"
        data = valid_form_data.copy()
        data["identical_finder_reporter"] = ""  # not identical
        data["finder_first_name"] = "Max"
        data["finder_last_name"] = "Finder"
        data["description"] = "Finder-Branch-Test"

        response = client.post(
            "/melden",
            data={**data, "photo": _create_test_image()},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data["success"] is True

        # Verify finder user was created
        sighting = session.scalar(
            select(TblMeldungen).where(
                TblMeldungen.anm_melder == "Finder-Branch-Test"
            )
        )
        assert sighting is not None
        link = session.scalar(
            select(TblMeldungUser).where(
                TblMeldungUser.id_meldung == sighting.id
            )
        )
        assert link is not None
        assert link.id_finder is not None  # finder was linked

    @patch("app.routes.report._process_uploaded_image")
    def test_submission_with_feedback_source(
        self, mock_process_image, client, valid_form_data, session
    ):
        """Feedback source + detail are saved to TblUserFeedback."""
        mock_process_image.return_value = "2025/2025-01-01/test.webp"
        data = valid_form_data.copy()
        data["feedback_source"] = "EVENT"
        data["feedback_detail"] = "Lange Nacht der Wissenschaften"
        data["description"] = "Feedback-Branch-Test"

        pre_feedback_count = session.scalar(
            select(func.count()).select_from(TblUserFeedback)
        )

        response = client.post(
            "/melden",
            data={**data, "photo": _create_test_image()},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data["success"] is True

        post_feedback_count = session.scalar(
            select(func.count()).select_from(TblUserFeedback)
        )
        assert post_feedback_count == pre_feedback_count + 1


# ============================================================================
# L. /melden/<usrid> POST — submission with existing user
# ============================================================================

class TestMeldenWithExistingUser:

    @patch("app.routes.report._process_uploaded_image")
    def test_unknown_usrid_creates_new_user(
        self, mock_process_image, client, valid_form_data, session
    ):
        """When usrid is in URL but doesn't exist in DB, create a new user."""
        mock_process_image.return_value = "2025/2025-01-01/test.webp"
        data = valid_form_data.copy()
        data["description"] = "Unknown-usrid-test"

        pre_user_count = session.scalar(
            select(func.count()).select_from(TblUsers)
        )

        response = client.post(
            "/melden/nonexistent_user_id_xyz",
            data={**data, "photo": _create_test_image()},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data["success"] is True

        post_user_count = session.scalar(
            select(func.count()).select_from(TblUsers)
        )
        assert post_user_count == pre_user_count + 1

    @patch("app.routes.report._process_uploaded_image")
    def test_existing_user_not_duplicated(
        self, mock_process_image, client, valid_form_data, session
    ):
        """When a valid usrid is in the URL, reuse that user — don't create a new one."""
        mock_process_image.return_value = "2025/2025-01-01/test.webp"

        # Create an existing user
        from app.tools.gen_user_id import get_new_id

        existing_user = TblUsers()
        existing_user.user_id = get_new_id()
        existing_user.user_name = "Testerin A."
        existing_user.user_rolle = "1"
        existing_user.user_kontakt = "anna@example.com"
        session.add(existing_user)
        session.commit()

        pre_user_count = session.scalar(
            select(func.count()).select_from(TblUsers)
        )

        response = client.post(
            f"/melden/{existing_user.user_id}",
            data={**valid_form_data, "photo": _create_test_image()},
            content_type="multipart/form-data",
        )

        assert response.status_code == 200
        json_data = response.get_json()
        assert json_data["success"] is True

        post_user_count = session.scalar(
            select(func.count()).select_from(TblUsers)
        )
        # User count should NOT increase — existing user reused
        assert post_user_count == pre_user_count
