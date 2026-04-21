import pytest
from unittest.mock import patch
from datetime import datetime
from app.database.models import TblMeldungen
from app.config import Config
from tests.helpers import set_client_user


@pytest.fixture
def authenticated_admin_client(client, session_with_user):
    """Fixture that provides a client with admin user session."""
    return set_client_user(client, "9999")


@pytest.fixture
def mock_sighting_factory(session):
    """Factory fixture that creates a mock sighting record in the test database.
    Returns a function to create multiple unique sightings."""

    test_ids = {}

    def _create_sighting(id_suffix=1):
        # Create a unique ID for each test
        test_id = 99990 + id_suffix

        # Make sure we don't create a duplicate ID
        if test_id in test_ids:
            test_id = max(test_ids.values()) + 1

        test_ids[id_suffix] = test_id

        # Create a test sighting with no approval date
        test_sighting = TblMeldungen(
            id=test_id,
            dat_fund_von=datetime.now().date(),
            dat_meld=datetime.now().date(),
            dat_bear=None,
            deleted=False,
            tiere=1,
            art_m=1,
            art_w=0,
            art_n=0,
            art_o=0,
            art_f=0,
            fo_zuordnung=1,
            fo_quelle="T",
            anm_melder="Test report for admin approval",
        )

        session.add(test_sighting)
        session.commit()

        return test_sighting

    return _create_sighting


@pytest.fixture
def mock_sighting(mock_sighting_factory):
    """Fixture that returns a single mock sighting record."""
    return mock_sighting_factory(1)


@pytest.mark.usefixtures("request_context")
class TestAdminApproval:
    """Test class for admin approval functionality."""

    @patch("app.routes.admin.send_email")
    def test_toggle_approve_sighting(
        self, mock_send_email, authenticated_admin_client, mock_sighting, session
    ):
        """Test that an admin can toggle the approval status of a sighting."""
        # Turn off email sending for this test
        with patch.object(Config, "REVIEWERMAIL", False):
            # Test approving the sighting
            response = authenticated_admin_client.post(
                f"/toggle_approve_sighting/{mock_sighting.id}",
                data={"filter_status": "all"},
                headers={"HX-Request": "true"},
            )

            # Check the response
            assert response.status_code == 200
            assert (
                response.headers.get("HX-Reswap") == "delete"
                or b'id="report-card-' in response.data
            )

            # Refresh the sighting from the database
            session.refresh(mock_sighting)

            # Check that the sighting is now approved
            assert mock_sighting.dat_bear is not None
            assert mock_sighting.bearb_id == "9999"

            # Test unapproving the sighting
            response = authenticated_admin_client.post(
                f"/toggle_approve_sighting/{mock_sighting.id}",
                data={"filter_status": "all"},
                headers={"HX-Request": "true"},
            )

            # Check the response
            assert response.status_code == 200
            assert (
                response.headers.get("HX-Reswap") == "delete"
                or b'id="report-card-' in response.data
            )

            # Refresh the sighting from the database
            session.refresh(mock_sighting)

            # Check that the sighting is now unapproved
            assert mock_sighting.dat_bear is None

            # Verify send_email was not called
            mock_send_email.assert_not_called()

    def test_approve_blocked_while_unkl_flag_set(
        self, authenticated_admin_client, mock_sighting_factory, session
    ):
        """A sighting flagged UNKL ("Unklar") cannot be approved — Bernd's case."""
        # Use a distinct id_suffix so this sighting does not collide with
        # test_toggle_approve_sighting's fixture when tests run in sequence.
        sighting = mock_sighting_factory(2)
        sighting.statuses = ["OPEN", "UNKL"]
        session.commit()

        with patch.object(Config, "REVIEWERMAIL", False):
            response = authenticated_admin_client.post(
                f"/toggle_approve_sighting/{sighting.id}",
                data={"filter_status": "all"},
                headers={"HX-Request": "true"},
            )

        assert response.status_code == 400

        session.refresh(sighting)
        # Status array and approval timestamp must be untouched.
        assert set(sighting.statuses) == {"OPEN", "UNKL"}
        assert sighting.dat_bear is None

    def test_toggle_approve_nonexistent_sighting(self, authenticated_admin_client):
        """Test that attempting to approve a nonexistent sighting returns a 404."""
        # Attempt to approve a sighting with an ID that doesn't exist
        response = authenticated_admin_client.post("/toggle_approve_sighting/99999999")

        # Check the response
        assert response.status_code == 404
