"""The database URL must survive credentials containing URL syntax.

Interpolating a password into the URL string silently misparses anything
containing @ / : # or %, so the app connects somewhere else or not at all.
"""

import importlib

import pytest
from sqlalchemy import make_url


@pytest.mark.parametrize(
    "password",
    [
        "kx@jj5/g",  # the example from SQLAlchemy's own docs
        "p:ss#word",
        "100%secret",
        "plain",
    ],
)
def test_password_survives_url_construction(monkeypatch, password):
    monkeypatch.setenv("POSTGRES_PASSWORD", password)
    monkeypatch.setenv("POSTGRES_USER", "mantis_user")
    monkeypatch.setenv("DATABASE_HOST", "db")
    monkeypatch.setenv("DATABASE_PORT", "5432")
    monkeypatch.setenv("POSTGRES_DB", "mantis_tracker")

    import app.config

    importlib.reload(app.config)
    url = make_url(app.config.Config.SQLALCHEMY_DATABASE_URI)

    assert url.password == password
    assert url.username == "mantis_user"
    assert url.host == "db"
    assert url.database == "mantis_tracker"

    # Leave the module holding the real environment for the rest of the session.
    monkeypatch.undo()
    importlib.reload(app.config)
