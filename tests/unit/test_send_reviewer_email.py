"""Unit tests for the reviewer email text renderer.

Tests app.tools.send_reviewer_email.rendertextmsg — a pure string formatter
that builds the notification email body sent to users after review.
"""

from app.tools.send_reviewer_email import rendertextmsg


def _make_mail_data(**overrides):
    """Build a minimal mail data dict with sensible defaults."""
    base = {
        "user_id": "abc123",
        "user_kontakt": "test@example.com",
        "latitude": "52.520",
        "longitude": "13.405",
        "plz": "10178",
        "ort": "Berlin",
        "strasse": "Alexanderplatz",
        "land": "Berlin",
        "kreis": "Mitte",
        "datum": "19.01.2025",
        "art_m": 1,
        "art_w": 0,
        "art_n": 0,
        "art_o": 0,
        "anm_bearbeiter": "Keine Anmerkung(en) vom Reviewer.",
    }
    base.update(overrides)
    return base


class TestRendertextmsg:

    def test_contains_greeting(self):
        text = rendertextmsg(_make_mail_data())
        assert "Mantis-Freund" in text

    def test_contains_user_contact(self):
        text = rendertextmsg(_make_mail_data(user_kontakt="melder@example.com"))
        assert "melder@example.com" in text

    def test_contains_coordinates(self):
        text = rendertextmsg(_make_mail_data(latitude="52.520", longitude="13.405"))
        assert "52.520" in text
        assert "13.405" in text

    def test_contains_location_fields(self):
        md = _make_mail_data(
            ort="Potsdam", strasse="Am Neuen Palais", land="Brandenburg", kreis="Potsdam"
        )
        text = rendertextmsg(md)
        assert "Potsdam" in text
        assert "Am Neuen Palais" in text
        assert "Brandenburg" in text

    def test_contains_date(self):
        text = rendertextmsg(_make_mail_data(datum="25.12.2025"))
        assert "25.12.2025" in text

    def test_contains_gender_counts(self):
        text = rendertextmsg(_make_mail_data(art_m=3, art_w=2, art_n=1, art_o=4))
        assert "3" in text
        assert "2" in text

    def test_contains_reviewer_note(self):
        note = "Schöner Fund, eindeutig Weibchen."
        text = rendertextmsg(_make_mail_data(anm_bearbeiter=note))
        assert note in text

    def test_contains_report_link_with_user_id(self):
        text = rendertextmsg(_make_mail_data(user_id="deadbeef42"))
        assert "report/deadbeef42" in text

    def test_contains_privacy_warning(self):
        text = rendertextmsg(_make_mail_data())
        assert "WICHTIGER HINWEIS" in text

    def test_contains_determination_reference(self):
        text = rendertextmsg(_make_mail_data())
        assert "bestimmung" in text
