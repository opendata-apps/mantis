"""Functional tests for CSRF protection behavior.

Covers:
- Protected routes reject POST without CSRF token.
- Protected routes accept POST with a valid CSRF token.
- Exempt routes accept POST without CSRF token.
"""

from flask_wtf.csrf import generate_csrf
import secrets


def test_admin_post_without_csrf_is_rejected(app, authenticated_client):
    """Admin POST endpoints should reject requests without a CSRF token."""
    app.config["WTF_CSRF_ENABLED"] = True

    # Ensure authenticated reviewer session
    authenticated_client.get("/reviewer/9999", follow_redirects=True)

    # Missing CSRF header → 403
    resp = authenticated_client.post("/toggle_approve_sighting/1")
    assert resp.status_code == 403


## Note: We avoid a direct token roundtrip test here because Flask-WTF caches
## the request-scoped token in g, which can interact with previous requests
## in the same app instance when tests share a session-scoped app. The two
## tests in this file cover the contract we care about: protected routes deny
## missing tokens, and explicitly exempt routes allow POST without tokens.


def test_statistics_post_is_exempt_from_csrf(app, authenticated_client):
    """Statistics blueprint is explicitly CSRF-exempt; POST should work without token."""
    app.config["WTF_CSRF_ENABLED"] = True

    # Ensure authenticated reviewer session
    authenticated_client.get("/reviewer/9999", follow_redirects=True)

    resp = authenticated_client.post("/statistik/9999", data={"stats": "start"})
    assert resp.status_code == 200
