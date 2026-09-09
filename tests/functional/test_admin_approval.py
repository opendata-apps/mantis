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

    @patch("app.routes.admin.reviewer.send_email")
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

            assert response.status_code == 200
            assert (
                response.headers.get("HX-Reswap") == "delete"
                or b'id="report-card-' in response.data
            )

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

            assert response.status_code == 200
            assert (
                response.headers.get("HX-Reswap") == "delete"
                or b'id="report-card-' in response.data
            )

            session.refresh(mock_sighting)

            # Check that the sighting is now unapproved
            assert mock_sighting.dat_bear is None

            mock_send_email.assert_not_called()

    @pytest.mark.parametrize(
        "flag, suffix",
        [("UNKL", 2), ("INFO", 3)],
    )
    def test_approve_blocked_while_review_flag_set(
        self,
        flag,
        suffix,
        authenticated_admin_client,
        mock_sighting_factory,
        session,
    ):
        """Active review flags (UNKL or INFO) block approval — Bernd's case."""
        # Distinct id_suffix avoids collision with test_toggle_approve_sighting.
        sighting = mock_sighting_factory(suffix)
        sighting.statuses = ["OPEN", flag]
        session.commit()

        response = authenticated_admin_client.post(
            f"/toggle_approve_sighting/{sighting.id}",
            data={"filter_status": "all"},
            headers={"HX-Request": "true"},
        )

        assert response.status_code == 400

        session.refresh(sighting)
        assert set(sighting.statuses) == {"OPEN", flag}
        assert sighting.dat_bear is None

    def test_toggle_approve_nonexistent_sighting(self, authenticated_admin_client):
        """Test that attempting to approve a nonexistent sighting returns a 404."""
        # Attempt to approve a sighting with an ID that doesn't exist
        response = authenticated_admin_client.post("/toggle_approve_sighting/99999999")

        assert response.status_code == 404


@pytest.fixture
def reported_sighting(session):
    """A report with the reporter link and contact the approval mail needs."""
    from app.database.models import (
        TblFundorte,
        TblFundortBeschreibung,
        TblMeldungUser,
        TblUsers,
    )
    from sqlalchemy import select

    reporter = TblUsers(
        user_id="mailtest-reporter",
        user_name="Mail Melder",
        user_kontakt="melder@example.com",
        user_rolle="1",
    )
    session.add(reporter)

    beschreibung = session.scalar(select(TblFundortBeschreibung))
    fundort = TblFundorte(
        mtb="3644",
        longitude="13.404954",
        latitude="52.520008",
        ort="Berlin",
        land="Berlin",
        kreis="Mitte",
        strasse="Alexanderplatz",
        plz=10178,
        amt="Amt Berlin",
        ablage="mailtest.jpg",
        beschreibung=beschreibung.id,
    )
    session.add(fundort)
    session.flush()

    sighting = TblMeldungen(
        dat_fund_von=datetime(2025, 7, 14).date(),
        dat_meld=datetime.now().date(),
        fo_zuordnung=fundort.id,
        statuses=["OPEN"],
        deleted=False,
        tiere=1,
        art_m=1,
        art_w=0,
        art_n=0,
        art_o=0,
        anm_bearbeiter="Klar ein Weibchen.",
    )
    session.add(sighting)
    session.flush()

    session.add(TblMeldungUser(id_meldung=sighting.id, id_user=reporter.id))
    session.commit()
    return sighting


@pytest.mark.usefixtures("request_context")
class TestApprovalMailPayload:
    """The approval route must hand the mail helper a payload it can render.

    The other mail tests feed ``send_email`` a hand-written dict, so nothing
    checked that the route actually assembles one. This drives the real chain:
    route -> payload -> rendertextmsg -> Message.
    """

    def test_approval_sends_renderable_mail(
        self, authenticated_admin_client, reported_sighting
    ):
        # Patch the live config, not the Config class: app.config is already
        # populated by the time the app exists, so rebinding the class
        # attribute would not reach the running application.
        app_config = authenticated_admin_client.application.config
        with patch.dict(app_config, {"REVIEWERMAIL": True}):
            with patch("app.tools.send_reviewer_email.mail.send") as mock_send:
                response = authenticated_admin_client.post(
                    f"/toggle_approve_sighting/{reported_sighting.id}",
                    data={"filter_status": "all"},
                    headers={"HX-Request": "true"},
                )

        assert response.status_code == 200
        mock_send.assert_called_once()

        message = mock_send.call_args.args[0]
        assert message.recipients == ["melder@example.com"]
        # Values must come from the right table, not from whichever one the
        # payload builder happened to write last.
        assert "13.404954" in message.body
        assert "52.520008" in message.body
        assert "Alexanderplatz" in message.body
        assert "14.07.2025" in message.body
        assert "Klar ein Weibchen." in message.body
        assert "/report/mailtest-reporter" in message.body
