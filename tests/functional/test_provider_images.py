"""Tests for provider image route access control.

Validates that /images/<path> enforces ownership:
- Unauthenticated: 403
- Reporter sees own images: 200
- Reporter cannot see other user's images: 403
- Reviewer sees all images: 200
"""

import os

import pytest
from datetime import datetime, timedelta
from sqlalchemy import select

from app.database.models import (
    TblMeldungen,
    TblFundorte,
    TblUsers,
    TblMeldungUser,
    TblFundortBeschreibung,
)
from tests.helpers import set_client_user, clear_client_session


class TestProviderImageAccess:
    """Test suite for /images/ route ownership enforcement."""

    IMAGE_FILE = "test_provider.webp"
    OTHER_IMAGE_FILE = "test_other_provider.webp"

    @pytest.fixture(autouse=True)
    def setup_test_data(self, app, session):
        """Create two reporters with separate images, plus a reviewer."""
        self.session = session
        self.upload_folder = app.config["UPLOAD_FOLDER"]

        # Ensure upload folder and test images exist
        os.makedirs(self.upload_folder, exist_ok=True)
        for img in (self.IMAGE_FILE, self.OTHER_IMAGE_FILE):
            path = os.path.join(self.upload_folder, img)
            if not os.path.exists(path):
                with open(path, "wb") as f:
                    # Minimal valid WebP file (RIFF header)
                    f.write(
                        b"RIFF\x24\x00\x00\x00WEBPVP8 "
                        b"\x18\x00\x00\x000\x01\x00\x9d\x01\x2a"
                        b"\x01\x00\x01\x00\x01\x40\x25\xa4\x00"
                        b"\x03p\x00\xfe\xfb\x94\x00\x00"
                    )

        # Reviewer (role 9) — use existing seed user
        self.reviewer = session.scalar(
            select(TblUsers).where(TblUsers.user_id == "9999")
        )

        # Reporter A
        self.reporter_a = session.scalar(
            select(TblUsers).where(TblUsers.user_id == "img_user_a")
        )
        if not self.reporter_a:
            self.reporter_a = TblUsers(
                user_id="img_user_a",
                user_name="Reporter A",
                user_kontakt="reporter_a@test.com",
                user_rolle="1",
            )
            session.add(self.reporter_a)

        # Reporter B (different email)
        self.reporter_b = session.scalar(
            select(TblUsers).where(TblUsers.user_id == "img_user_b")
        )
        if not self.reporter_b:
            self.reporter_b = TblUsers(
                user_id="img_user_b",
                user_name="Reporter B",
                user_kontakt="reporter_b@test.com",
                user_rolle="1",
            )
            session.add(self.reporter_b)

        session.flush()

        beschreibung = session.scalar(
            select(TblFundortBeschreibung).where(TblFundortBeschreibung.id == 1)
        )

        # Location + sighting owned by Reporter A
        loc_a = TblFundorte(
            mtb="3644",
            longitude="13.4",
            latitude="52.5",
            ort="CityA",
            land="Brandenburg",
            kreis="DistrictA",
            strasse="StreetA",
            plz=10000,
            amt="AmtA",
            ablage=self.IMAGE_FILE,
            beschreibung=beschreibung.id,
        )
        session.add(loc_a)
        session.flush()

        sighting_a = TblMeldungen(
            dat_fund_von=datetime.now().date() - timedelta(days=5),
            dat_meld=datetime.now().date(),
            fo_zuordnung=loc_a.id,
            art_m=1,
            art_w=0,
            art_n=0,
            art_o=0,
        )
        session.add(sighting_a)
        session.flush()

        session.add(
            TblMeldungUser(id_meldung=sighting_a.id, id_user=self.reporter_a.id)
        )

        # Location + sighting owned by Reporter B
        loc_b = TblFundorte(
            mtb="3644",
            longitude="13.5",
            latitude="52.6",
            ort="CityB",
            land="Brandenburg",
            kreis="DistrictB",
            strasse="StreetB",
            plz=10001,
            amt="AmtB",
            ablage=self.OTHER_IMAGE_FILE,
            beschreibung=beschreibung.id,
        )
        session.add(loc_b)
        session.flush()

        sighting_b = TblMeldungen(
            dat_fund_von=datetime.now().date() - timedelta(days=3),
            dat_meld=datetime.now().date(),
            fo_zuordnung=loc_b.id,
            art_m=0,
            art_w=1,
            art_n=0,
            art_o=0,
        )
        session.add(sighting_b)
        session.flush()

        session.add(
            TblMeldungUser(id_meldung=sighting_b.id, id_user=self.reporter_b.id)
        )

        session.commit()

        yield

        # Clean up test image files
        for img in (self.IMAGE_FILE, self.OTHER_IMAGE_FILE):
            path = os.path.join(self.upload_folder, img)
            if os.path.exists(path):
                os.remove(path)

    def test_unauthenticated_access_returns_403(self, client):
        """No session → 403."""
        clear_client_session(client)
        response = client.get(f"/images/{self.IMAGE_FILE}")
        assert response.status_code == 403

    def test_invalid_user_id_returns_403(self, client):
        """Session with non-existent user_id → 403."""
        set_client_user(client, "nonexistent_user_id_xyz")
        response = client.get(f"/images/{self.IMAGE_FILE}")
        assert response.status_code == 403

    def test_reporter_can_access_own_image(self, client):
        """Reporter A can see their own image."""
        set_client_user(client, "img_user_a")
        response = client.get(f"/images/{self.IMAGE_FILE}")
        assert response.status_code == 200

    def test_reporter_cannot_access_other_users_image(self, client):
        """Reporter A cannot see Reporter B's image."""
        set_client_user(client, "img_user_a")
        response = client.get(f"/images/{self.OTHER_IMAGE_FILE}")
        assert response.status_code == 403

    def test_reporter_b_can_access_own_image(self, client):
        """Reporter B can see their own image."""
        set_client_user(client, "img_user_b")
        response = client.get(f"/images/{self.OTHER_IMAGE_FILE}")
        assert response.status_code == 200

    def test_reporter_b_cannot_access_other_users_image(self, client):
        """Reporter B cannot see Reporter A's image."""
        set_client_user(client, "img_user_b")
        response = client.get(f"/images/{self.IMAGE_FILE}")
        assert response.status_code == 403

    def test_reviewer_can_access_any_image(self, client):
        """Reviewer (role 9) can see all images."""
        set_client_user(client, "9999")
        response_a = client.get(f"/images/{self.IMAGE_FILE}")
        response_b = client.get(f"/images/{self.OTHER_IMAGE_FILE}")
        assert response_a.status_code == 200
        assert response_b.status_code == 200

    def test_nonexistent_image_returns_404(self, client):
        """Authenticated user requesting non-existent file gets 404, not 403."""
        set_client_user(client, "9999")
        response = client.get("/images/does_not_exist.webp")
        assert response.status_code == 404
