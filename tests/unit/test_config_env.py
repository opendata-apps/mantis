from app.config import _env_or_default


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
