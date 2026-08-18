"""The form must only accept addresses the mail path can actually reach.

A reviewer mail is sent after the report is committed, so an address smtplib
cannot put in an envelope produces a saved report, a reviewer who sees success
and a reporter who never hears back — the failure recorded in production as
``'ascii' codec can't encode character '\\xf6'``.
"""

import pytest

from app.forms import MantisSightingForm

BASE = {
    "report_first_name": "Erika",
    "report_last_name": "Musterfrau",
    "fund_city": "Potsdam",
    "sighting_date": "2026-08-01",
}


def _validate_email(app, address):
    with app.test_request_context(method="POST", data={**BASE, "email": address}):
        form = MantisSightingForm(meta={"csrf": False})
        form.validate()
        return form.email


@pytest.mark.parametrize("address", ["melder@web.de", "a.b+c@sub.example.co.uk"])
def test_ordinary_addresses_pass_through_unchanged(app, address):
    field = _validate_email(app, address)

    assert field.errors == []
    assert field.data == address


def test_umlaut_in_the_local_part_is_rejected(app):
    """Needs SMTPUTF8 end to end, which this path does not have."""
    field = _validate_email(app, "müller@web.de")

    assert field.errors


def test_umlaut_domain_is_kept_but_stored_as_punycode(app):
    """A real, deliverable address — only the wire form differs."""
    field = _validate_email(app, "test@müller.de")

    assert field.errors == []
    assert field.data == "test@xn--mller-kva.de"
    field.data.encode("ascii")


def test_an_invalid_address_still_reports_the_german_message(app):
    field = _validate_email(app, "keine-adresse")

    assert field.errors == ["Bitte geben Sie eine gültige E-Mail-Adresse ein."]


def test_empty_stays_empty(app):
    """Contact is optional on the report form."""
    field = _validate_email(app, "")

    assert field.errors == []
    assert not field.data
