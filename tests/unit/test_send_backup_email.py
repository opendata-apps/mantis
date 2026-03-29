"""Unit tests for the reviewer email text renderer.

Tests app.tools.send_reviewer_email.rendertextmsg — a pure string formatter
that builds the notification email body sent to users after review.
"""

from app.tools.send_backup_email import rendertextmsg


def _make_mail_data(**overrides):
    """Build a minimal mail data dict with sensible defaults."""
    base = {
        "user_id": "abc123",
        "sender": "test@example.com",
        "year": "2025",
        "backup": "backup_2025.zip"
    }
    base.update(overrides)
    return base


class TestRendertextmsg:

    def test_contains_greeting(self):
        text = rendertextmsg(_make_mail_data())
        assert "Lieber Reviewer" in text


    def test_contains__download_link(self):
        text = rendertextmsg(_make_mail_data())
        assert "https://gottesanbeterin-gesucht.de/save/backup_2025.zip" in text

    def test_contains_privacy_warning(self):
        text = rendertextmsg(_make_mail_data())
        assert "Ihr Team vom Mantis-Portal" in text

