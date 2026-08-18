import smtplib

import pytest
from flask_mail import sanitize_address

from app.config import _env_or_default, _resolve_mail_sender


def test_env_or_default_uses_default_for_missing_value(monkeypatch):
    monkeypatch.delenv("MAIL_SERVER", raising=False)

    assert _env_or_default("MAIL_SERVER", "mail.mantis-projekt.de") == (
        "mail.mantis-projekt.de"
    )


def test_env_or_default_uses_default_for_empty_value(monkeypatch):
    monkeypatch.setenv("MAIL_SERVER", "")

    assert _env_or_default("MAIL_SERVER", "mail.mantis-projekt.de") == (
        "mail.mantis-projekt.de"
    )


def test_env_or_default_keeps_configured_value(monkeypatch):
    monkeypatch.setenv("MAIL_SERVER", "smtp.example.test")

    assert _env_or_default("MAIL_SERVER", "mail.mantis-projekt.de") == (
        "smtp.example.test"
    )


# The value that shipped in the production .env: a Python tuple literal, which
# os.getenv hands back verbatim as the address half of the sender.
BROKEN_SENDER = '("Matis-Projekt", "meldebestaetigung@gottesanbeterin-gesucht.de")'


def test_resolve_mail_sender_accepts_plain_address():
    assert _resolve_mail_sender("Mantis-Projekt", "post@example.test") == (
        "Mantis-Projekt",
        "post@example.test",
    )


def test_resolve_mail_sender_rejects_tuple_literal():
    with pytest.raises(ValueError, match="plain email address"):
        _resolve_mail_sender("Mantis-Projekt", BROKEN_SENDER)


def test_broken_sender_would_have_emptied_the_smtp_envelope():
    """Why the guard exists: nothing downstream complains, the mail just dies.

    smtplib cannot parse the address out, falls back to the null sender, and
    every reviewer mail leaves looking like a bounce.
    """
    envelope = smtplib.quoteaddr(sanitize_address(("Mantis-Projekt", BROKEN_SENDER)))

    assert envelope == "<>"


def test_resolved_sender_keeps_the_smtp_envelope_intact():
    envelope = smtplib.quoteaddr(
        sanitize_address(_resolve_mail_sender("Mantis-Projekt", "post@example.test"))
    )

    assert envelope == "<post@example.test>"
