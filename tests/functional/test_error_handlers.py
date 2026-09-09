"""The 500 handler must run for uncaught exceptions, not just abort(500).

Flask picks error handlers by exception class hierarchy, so an
``@app.errorhandler(Exception)`` shadows the 500 handler for everything that is
not an HTTPException. While one existed, `internal_server_error` only ran for
the single explicit abort(500) and its JSON negotiation was dead — fetch/HTMX
callers got an HTML error page.
https://flask.palletsprojects.com/en/stable/errorhandling/
"""

import pytest

from app import create_app
from tests.test_config import Config as TestConfig


@pytest.fixture
def crashing_client():
    """Own app: the shared one has served requests, so it takes no new routes."""
    app = create_app(TestConfig)

    # Reproduce production dispatch: TESTING=True would otherwise re-raise
    # instead of invoking the handler. (DEBUG is pinned off in TestConfig.)
    app.config["PROPAGATE_EXCEPTIONS"] = False

    @app.route("/__crash")
    def crash():
        raise ValueError("boom")

    return app.test_client()


def test_uncaught_exception_answers_json_clients_with_json(crashing_client):
    resp = crashing_client.get("/__crash", headers={"Accept": "application/json"})

    assert resp.status_code == 500
    assert resp.is_json, f"expected JSON, got {resp.content_type}"
    assert resp.get_json() == {"error": "Internal server error"}


def test_uncaught_exception_answers_browsers_with_the_error_page(crashing_client):
    resp = crashing_client.get("/__crash", headers={"Accept": "text/html"})

    assert resp.status_code == 500
    assert "text/html" in resp.content_type
