"""A reporter's history must hang off their own link, not their address.

Guards the scoping rule stated at the query in app/routes/provider.py.

"""

import os
import re
from datetime import datetime, timedelta

import pytest
from bs4 import BeautifulSoup
from sqlalchemy import select

from app.database.models import (
    TblFundortBeschreibung,
    TblFundorte,
    TblMeldungen,
    TblMeldungUser,
    TblUsers,
)
from tests.helpers import build_valid_report_form_data, make_test_image
from tests.test_config import Config as TestConfig

REPORTER_COOKIE = TestConfig.REMEMBER_COOKIE_NAME
VICTIM_EMAIL = "victim@example.com"
VICTIM_LAT = "51.111111"
VICTIM_LON = "11.222222"

# Minimal valid WebP (RIFF header) — send_from_directory only needs a real file.
WEBP_BYTES = (
    b"RIFF\x24\x00\x00\x00WEBPVP8 "
    b"\x18\x00\x00\x000\x01\x00\x9d\x01\x2a"
    b"\x01\x00\x01\x00\x01\x40\x25\xa4\x00"
    b"\x03p\x00\xfe\xfb\x94\x00\x00"
)


@pytest.fixture
def upload_folder(app):
    """Create this test's isolated upload root."""
    folder = app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    return folder


def _seed_victim(session, upload_folder, *, usrid, image, contact=VICTIM_EMAIL):
    """A reporter with one report carrying exact coordinates and a photo."""
    with open(os.path.join(upload_folder, image), "wb") as f:
        f.write(WEBP_BYTES)

    beschreibung = session.scalar(select(TblFundortBeschreibung).limit(1))
    victim = TblUsers(
        user_id=usrid,
        user_name="Opfer O.",
        user_kontakt=contact,
        user_rolle="1",
    )
    fundort = TblFundorte(
        mtb="3644",
        longitude=VICTIM_LON,
        latitude=VICTIM_LAT,
        ort="Opferstadt",
        land="Brandenburg",
        kreis="Opferkreis",
        strasse="Opferweg 1",
        plz=14467,
        amt="AmtO",
        ablage=image,
        beschreibung=beschreibung.id,
    )
    session.add_all([victim, fundort])
    session.flush()

    meldung = TblMeldungen(
        dat_fund_von=datetime.now().date() - timedelta(days=9),
        dat_meld=datetime.now().date(),
        fo_zuordnung=fundort.id,
        art_m=1,
        art_w=0,
        art_n=0,
        art_o=0,
    )
    session.add(meldung)
    session.flush()

    session.add(TblMeldungUser(id_meldung=meldung.id, id_user=victim.id))
    session.commit()
    return victim


def _report_of(session, reporter):
    return session.scalar(
        select(TblMeldungUser.id_meldung).where(TblMeldungUser.id_user == reporter.id)
    )


def _modal_reporter(client, report_id):
    """The report count and the reporter link the reviewer modal shows."""
    page = BeautifulSoup(client.get(f"/modal/{report_id}").data, "html.parser")
    label = page.find("span", string="Anzahl Meldungen")
    assert label is not None
    count = label.find_next_sibling("span")
    link = page.find("a", title=re.compile("Meldungen dieses Melders"))
    assert count is not None
    assert link is not None
    return count.get_text(strip=True), str(link["href"])


class TestReviewerSeesTheWholeAddress:
    """Reviewers follow a reporter across every link filed under one address."""

    def test_reporter_link_lists_every_link_of_the_address_newest_first(
        self, authenticated_client, session, upload_folder
    ):
        older = _seed_victim(
            session, upload_folder, usrid="addr-older", image="older.webp"
        )
        newer = _seed_victim(
            session,
            upload_folder,
            usrid="addr-newer",
            image="newer.webp",
            contact="Victim@EXAMPLE.com",
        )
        _seed_victim(
            session,
            upload_folder,
            usrid="addr-other",
            image="other.webp",
            contact="other@example.com",
        )

        count, href = _modal_reporter(authenticated_client, _report_of(session, older))
        listing = BeautifulSoup(authenticated_client.get(href).data, "html.parser")

        assert count == "2"
        assert [card["id"] for card in listing.select(".report-card")] == [
            f"report-card-{_report_of(session, newer)}",
            f"report-card-{_report_of(session, older)}",
        ]

    def test_a_blank_address_joins_no_one(
        self, authenticated_client, session, upload_folder
    ):
        first = _seed_victim(
            session, upload_folder, usrid="blank-first", image="b1.webp", contact=""
        )
        _seed_victim(
            session, upload_folder, usrid="blank-second", image="b2.webp", contact=""
        )

        count, _ = _modal_reporter(authenticated_client, _report_of(session, first))

        assert count == "1"


def _submit_as(client, email, **overrides):
    """File a sighting through the public form."""
    data = build_valid_report_form_data(email=email, **overrides)
    response = client.post(
        "/melden",
        data={**data, "photo": make_test_image(fmt="webp", name="upload.webp")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200, response.data[:400]
    assert response.get_json()["success"] is True


def _link_from_success(client):
    """Read the reporter's own usrid off /success the way a browser would."""
    page = client.get("/success")
    assert page.status_code == 200
    soup = BeautifulSoup(page.data, "html.parser")
    for anchor in soup.find_all("a", href=True):
        href = str(anchor["href"])
        if "/sichtungen/" in href:
            return href.rsplit("/", 1)[1]
    return None


class TestAddressIsNotACredential:
    """Knowing an address must not unlock the reports filed under it."""

    def test_submitting_under_a_known_address_does_not_expose_its_reports(
        self, client, session, upload_folder
    ):
        _seed_victim(
            session, upload_folder, usrid="victim_plain", image="victim_plain.webp"
        )

        _submit_as(client, VICTIM_EMAIL)
        stranger = _link_from_success(client)
        assert stranger
        assert stranger != "victim_plain"

        listing = client.get(f"/sichtungen/{stranger}")
        assert listing.status_code == 200
        assert VICTIM_LAT.encode() not in listing.data
        assert VICTIM_LON.encode() not in listing.data
        assert b"victim_plain.webp" not in listing.data

        assert (
            client.get(f"/sichtungen/{stranger}/images/victim_plain.webp").status_code
            == 403
        )

    def test_normalizing_legacy_contacts_does_not_widen_access(
        self, client, session, upload_folder
    ):
        """The one-off contact repair must not double as an access grant.

        Normalizing ``victim@EXAMPLE.COM`` makes it collide with a fresh
        submission, which only matters if that column decides access.
        """
        from scripts.normalize_contact_domains import main

        _seed_victim(
            session,
            upload_folder,
            usrid="victim_legacy",
            image="victim_legacy.webp",
            contact="victim@EXAMPLE.COM",
        )

        _submit_as(client, VICTIM_EMAIL)
        stranger = _link_from_success(client)

        with client.application.app_context():
            main(apply_changes=True)
        victim = session.scalar(
            select(TblUsers).where(TblUsers.user_id == "victim_legacy")
        )
        assert victim.user_kontakt == VICTIM_EMAIL, "precondition: rows now collide"

        listing = client.get(f"/sichtungen/{stranger}")
        assert VICTIM_LAT.encode() not in listing.data
        assert (
            client.get(f"/sichtungen/{stranger}/images/victim_legacy.webp").status_code
            == 403
        )


class TestBrowserKeepsTheReporterLink:
    """A repeat submission must continue the identity, not mint a new one."""

    def test_second_report_from_the_same_browser_keeps_one_history(self, client):
        _submit_as(client, "treue@example.com", fund_city="Erststadt")
        first = _link_from_success(client)
        assert client.get_cookie(REPORTER_COOKIE) is not None

        _submit_as(client, "treue@example.com", fund_city="Zweitstadt")
        second = _link_from_success(client)
        assert second == first, "same browser, same address → same identity"

        listing = client.get(f"/sichtungen/{first}")
        assert b"Erststadt" in listing.data
        assert b"Zweitstadt" in listing.data

    def test_a_different_address_on_a_shared_device_starts_its_own_history(
        self, client
    ):
        _submit_as(client, "erste@example.com", fund_city="Erststadt")
        first = _link_from_success(client)

        _submit_as(client, "zweite@example.com", fund_city="Zweitstadt")
        second = _link_from_success(client)
        assert second != first

        assert b"Erststadt" not in client.get(f"/sichtungen/{second}").data
        assert b"Zweitstadt" not in client.get(f"/sichtungen/{first}").data

    def test_a_forged_remember_cookie_is_rejected(self, client, session, upload_folder):
        """Naming a reporter in the cookie is not the same as holding their link.

        Flask-Login signs the cookie, so a value the server never issued is
        discarded rather than trusted.
        """
        _seed_victim(
            session, upload_folder, usrid="victim_cookie", image="victim_cookie.webp"
        )
        client.set_cookie(REPORTER_COOKIE, "victim_cookie")

        _submit_as(client, VICTIM_EMAIL)
        stranger = _link_from_success(client)
        assert stranger != "victim_cookie"

        listing = client.get(f"/sichtungen/{stranger}")
        assert VICTIM_LAT.encode() not in listing.data
        assert (
            client.get(f"/sichtungen/{stranger}/images/victim_cookie.webp").status_code
            == 403
        )

    def test_opening_your_own_page_remembers_the_link(self, client):
        _submit_as(client, "rueckkehr@example.com", fund_city="Erststadt")
        mine = _link_from_success(client)

        # A new device: no cookie, but the link from the determination mail.
        other = client.application.test_client()
        assert other.get_cookie(REPORTER_COOKIE) is None
        other.get(f"/sichtungen/{mine}")
        assert other.get_cookie(REPORTER_COOKIE) is not None

        _submit_as(other, "rueckkehr@example.com", fund_city="Zweitstadt")
        listing = other.get(f"/sichtungen/{mine}")
        assert b"Erststadt" in listing.data
        assert b"Zweitstadt" in listing.data


class TestSubmissionKeepsTheLogin:
    """Filing a sighting must not replace the identity the browser holds."""

    def test_a_reviewer_who_files_a_sighting_stays_a_reviewer(self, client):
        client.get("/reviewer/9999")

        _submit_as(client, "reviewerin@example.com", fund_city="Feldstadt")

        page = client.get("/reviewer?statusInput=offen&sort_order=id_desc")
        assert page.status_code == 200


class TestOwnReportsStayReachable:
    """The reporter's own link keeps working for the reports that belong to it."""

    def test_reporter_sees_the_report_they_just_filed(self, client):
        _submit_as(client, "eigene@example.com", fund_city="Eigenstadt")
        mine = _link_from_success(client)
        assert mine

        listing = client.get(f"/sichtungen/{mine}")
        assert listing.status_code == 200
        assert b"Eigenstadt" in listing.data

    def test_a_second_reporter_on_a_shared_device_sees_their_own_photo(self, client):
        # The browser stays logged in as the first reporter; the second one
        # holds only the link to their own page.
        _submit_as(client, "erste@example.com", fund_city="Erststadt")
        _submit_as(client, "zweite@example.com", fund_city="Zweitstadt")
        mine = _link_from_success(client)

        listing = client.get(f"/sichtungen/{mine}")
        soup = BeautifulSoup(listing.data, "html.parser")
        photos = [str(img["src"]) for img in soup.select("#reportContainer img")]

        assert [client.get(src).status_code for src in photos] == [200]

    def test_repeat_report_through_the_link_joins_the_same_history(self, client):
        _submit_as(client, "wieder@example.com", fund_city="Erststadt")
        mine = _link_from_success(client)

        data = build_valid_report_form_data(
            email="wieder@example.com", fund_city="Zweitstadt"
        )
        response = client.post(
            f"/melden/{mine}",
            data={**data, "photo": make_test_image(fmt="webp", name="upload.webp")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200

        listing = client.get(f"/sichtungen/{mine}")
        assert b"Erststadt" in listing.data
        assert b"Zweitstadt" in listing.data

    def test_own_page_lists_the_newest_report_first(self, client):
        _submit_as(client, "reihe@example.com", fund_city="Erststadt")
        mine = _link_from_success(client)
        data = build_valid_report_form_data(
            email="reihe@example.com", fund_city="Zweitstadt"
        )
        client.post(
            f"/melden/{mine}",
            data={**data, "photo": make_test_image(fmt="webp", name="upload.webp")},
            content_type="multipart/form-data",
        )

        listing = client.get(f"/sichtungen/{mine}").data

        assert listing.index(b"Zweitstadt") < listing.index(b"Erststadt")
