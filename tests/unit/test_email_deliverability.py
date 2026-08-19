"""Addresses follow the shape python-email-validator documents.

Normalized in the database, punycode on the wire. Reviewer mail is sent after
the report is committed, so an address smtplib cannot put in an envelope leaves
a saved report and a reporter who never hears back — the failure recorded in
production as ``'ascii' codec can't encode character '\\xf6'``.
"""

import pytest

from app.forms import MantisSightingForm
from app.routes.report import _create_user

BASE = {
    "report_first_name": "Erika",
    "report_last_name": "Musterfrau",
    "fund_city": "Potsdam",
    "sighting_date": "2026-08-01",
}


def _email_field(app, address):
    with app.test_request_context(method="POST", data={**BASE, "email": address}):
        form = MantisSightingForm(meta={"csrf": False})
        form.validate()
        return form.email


@pytest.mark.parametrize("address", ["melder@web.de", "a.b+c@sub.example.co.uk"])
def test_ordinary_addresses_are_accepted(app, address):
    assert _email_field(app, address).errors == []


def test_umlaut_in_the_local_part_is_refused(app):
    """Would need SMTPUTF8 along the whole path, which flask-mail has not."""
    assert _email_field(app, "müller@web.de").errors


def test_umlaut_domain_is_accepted(app):
    """A real, deliverable address; only its wire form differs."""
    assert _email_field(app, "test@müller.de").errors == []


def test_an_invalid_address_reports_the_german_message(app):
    assert _email_field(app, "keine-adresse").errors == [
        "Bitte geben Sie eine gültige E-Mail-Adresse ein."
    ]


def test_storage_keeps_the_address_the_reporter_knows(app):
    """normalized, per the library: domain lowercased, local part untouched."""
    user = _create_user("Erika", "Musterfrau", "Melder@Müller.DE")

    assert user.user_kontakt == "Melder@müller.de"


def test_storage_folds_case_so_one_mailbox_is_one_row(app):
    first = _create_user("Erika", "Musterfrau", "melder@WEB.de")
    second = _create_user("Erika", "Musterfrau", "melder@web.de")

    assert first.user_kontakt == second.user_kontakt


def test_a_blank_contact_stays_blank(app):
    """Contact is optional on the report form."""
    assert not _create_user("Erika", "Musterfrau", "").user_kontakt


def test_the_envelope_carries_punycode(app, monkeypatch):
    """The conversion belongs immediately before submission, not in storage."""
    from app.tools import send_reviewer_email as sre

    sent = {}
    monkeypatch.setattr(sre.mail, "send", lambda msg: sent.update(to=msg.recipients))

    with app.app_context():
        sre.send_email(_reviewer_payload("test@müller.de"))

    assert sent["to"] == ["test@xn--mller-kva.de"]
    sent["to"][0].encode("ascii")


def test_an_undeliverable_recipient_is_rejected_before_the_message_is_built(app):
    """Rows predating the form's SMTPUTF8 guard still reach send_email. Without
    the guard, Message takes recipients=[None] and fails far from the cause."""
    from email_validator import EmailNotValidError

    from app.tools import send_reviewer_email as sre

    with app.app_context():
        with pytest.raises(EmailNotValidError, match="Internationalized characters"):
            sre.send_email(_reviewer_payload("müller@web.de"))


def _reviewer_payload(contact):
    from datetime import datetime

    return {
        "user_id": "abc123",
        "user_kontakt": contact,
        "anm_bearbeiter": "",
        "dat_fund_von": datetime(2026, 8, 1),
        "latitude": "52.4",
        "longitude": "13.0",
        "plz": "14467",
        "ort": "Potsdam",
        "strasse": "Teststr.",
        "land": "Brandenburg",
        "kreis": "Potsdam",
        "art_m": 1,
        "art_w": 0,
        "art_n": 0,
        "art_o": 0,
    }
