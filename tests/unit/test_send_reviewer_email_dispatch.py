"""Tests for the ``send_email`` dispatch helper.

Complements ``test_send_reviewer_email.py``, which exercises the pure
``rendertextmsg`` text formatter. These tests cover ``send_email``: the
wrapper that normalises the review note, formats the date, and hands a
``flask_mail.Message`` to the Mail extension.

The Mail extension is patched so no SMTP connection is attempted.
"""

from datetime import date
from unittest.mock import patch

import pytest

from app.tools.send_reviewer_email import send_email


def _mail_payload(**overrides):
    base = {
        "user_id": "reporter-123",
        "user_kontakt": "reporter@example.com",
        "anm_bearbeiter": "",
        "dat_fund_von": date(2025, 7, 14),
        "latitude": "52.500",
        "longitude": "13.400",
        "plz": "10178",
        "ort": "Berlin",
        "strasse": "Alexanderplatz",
        "land": "Berlin",
        "kreis": "Mitte",
        "art_m": 1,
        "art_w": 0,
        "art_n": 0,
        "art_o": 0,
    }
    base.update(overrides)
    return base


@pytest.mark.usefixtures("request_context")
class TestSendEmailDispatch:
    def test_sends_to_user_kontakt(self):
        payload = _mail_payload(user_kontakt="melder@example.com")
        with patch("app.tools.send_reviewer_email.mail.send") as mock_send:
            send_email(payload)

        mock_send.assert_called_once()
        msg = mock_send.call_args.args[0]
        assert msg.recipients == ["melder@example.com"]

    def test_subject_fixed(self):
        with patch("app.tools.send_reviewer_email.mail.send") as mock_send:
            send_email(_mail_payload())
        msg = mock_send.call_args.args[0]
        assert "Meldung überprüft" in msg.subject

    def test_empty_note_produces_default_text(self):
        """When the reviewer did not leave a note, the body must carry the
        German fallback — not an empty string. Guards against regression
        where the template would render an awkward blank line."""
        with patch("app.tools.send_reviewer_email.mail.send") as mock_send:
            send_email(_mail_payload(anm_bearbeiter=""))
        body = mock_send.call_args.args[0].body
        assert "Keine Anmerkung(en) vom Reviewer." in body

    def test_present_note_prefixed_with_label(self):
        with patch("app.tools.send_reviewer_email.mail.send") as mock_send:
            send_email(_mail_payload(anm_bearbeiter="Klar Weibchen."))
        body = mock_send.call_args.args[0].body
        assert "Anmerkung(en) vom Reviewer: Klar Weibchen." in body

    def test_date_formatted_german(self):
        with patch("app.tools.send_reviewer_email.mail.send") as mock_send:
            send_email(_mail_payload(dat_fund_von=date(2025, 7, 14)))
        body = mock_send.call_args.args[0].body
        # German format DD.MM.YYYY
        assert "14.07.2025" in body

    def test_does_not_mutate_caller_dict(self):
        """``send_email`` reassigns ``anm_bearbeiter`` and adds ``datum``;
        it should do so on its own copy so callers can reuse the payload.
        """
        payload = _mail_payload(anm_bearbeiter="")
        original = dict(payload)
        with patch("app.tools.send_reviewer_email.mail.send"):
            send_email(payload)
        # Caller dict stays untouched
        assert payload == original
        assert "datum" not in payload
