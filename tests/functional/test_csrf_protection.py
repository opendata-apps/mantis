"""Functional tests for CSRF protection behavior.

Covers:
- Protected routes reject POST without CSRF token (admin and statistics).
"""

from bs4 import BeautifulSoup
import pytest

from app.database.models import TblMeldungen


@pytest.fixture
def test_config(test_config):
    class CSRFConfig(test_config):
        WTF_CSRF_ENABLED = True

    return CSRFConfig


def test_admin_post_without_csrf_is_rejected(authenticated_client):
    """Admin POST endpoints should reject requests without a CSRF token."""
    authenticated_client.get("/reviewer/9999", follow_redirects=True)
    resp = authenticated_client.post("/toggle_approve_sighting/1")
    assert resp.status_code == 403


def test_csrf_token_from_reviewer_page_allows_saved_approval(
    authenticated_client, session
):
    report = session.get(TblMeldungen, 1)
    assert report is not None
    report.statuses = ["OPEN"]
    session.commit()

    page = authenticated_client.get("/reviewer", follow_redirects=True)
    assert page.status_code == 200
    token = BeautifulSoup(page.text, "html.parser").select_one(
        'meta[name="csrf-token"]'
    )
    assert token is not None
    response = authenticated_client.post(
        "/toggle_approve_sighting/1",
        headers={"X-CSRFToken": str(token["content"])},
    )
    assert response.status_code == 200
    session.refresh(report)
    assert report.is_approved


def test_statistics_post_without_csrf_is_rejected(authenticated_client):
    """Statistics POST endpoints should reject requests without a CSRF token."""
    authenticated_client.get("/reviewer/9999", follow_redirects=True)
    resp = authenticated_client.post("/statistik", data={"stats": "start"})
    assert resp.status_code == 403


def test_htmx_csrf_failure_returns_hx_redirect(authenticated_client):
    """HTMX requests that fail CSRF should get HX-Redirect, not a full HTML page."""
    authenticated_client.get("/reviewer/9999", follow_redirects=True)
    resp = authenticated_client.post(
        "/toggle_approve_sighting/1",
        headers={"HX-Request": "true"},
    )
    assert resp.status_code == 403
    assert resp.headers["HX-Redirect"] == "/"
