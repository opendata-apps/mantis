"""Tests for reviewer dashboard auth and date type filter.

Test data (from demodata/filldb.py):
- User '9999' has user_rolle='9' (reviewer)
- 20 reports: dat_fund_von in 2024, dat_meld on 2025-02-01 / 2025-02-02
- Statuses: APPR (3), OPEN (14), DEL (1), UNKL (2), INFO (1)
"""

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _login_session(client, user_id="9999"):
    """Set user_id in the Flask session for subsequent requests."""
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


# ---------------------------------------------------------------------------
# Auth: session-based reviewer access
# ---------------------------------------------------------------------------


class TestReviewerAuth:
    """Verify unified auth: URL-based login + session-based fallback."""

    def test_reviewer_without_session_returns_401(self, client):
        """GET /reviewer with no session should return 401 (session expired)."""
        response = client.get("/reviewer")
        assert response.status_code == 401

    def test_reviewer_with_valid_session(self, client):
        """GET /reviewer with a valid reviewer session should load the dashboard."""
        _login_session(client, "9999")
        response = client.get(
            "/reviewer?statusInput=offen&sort_order=id_desc", follow_redirects=True
        )
        assert response.status_code == 200
        assert b"Admin Panel" in response.data

    def test_reviewer_url_login_sets_session(self, client):
        """GET /reviewer/<usrid> should set the session and load the dashboard."""
        response = client.get(
            "/reviewer/9999?statusInput=offen&sort_order=id_desc",
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Admin Panel" in response.data

        # Session should now be set — /reviewer without usrid should work
        response2 = client.get(
            "/reviewer?statusInput=offen&sort_order=id_desc", follow_redirects=True
        )
        assert response2.status_code == 200

    def test_reviewer_invalid_usrid_returns_403(self, client):
        """GET /reviewer/<invalid-usrid> should return 403."""
        response = client.get("/reviewer/nonexistent-user-id")
        assert response.status_code == 403

    def test_reviewer_non_reviewer_role_returns_403(self, client):
        """GET /reviewer/<usrid> with non-reviewer role should return 403."""
        # User with id starting with 'e40ada...' has user_rolle='2' (not a reviewer)
        response = client.get(
            "/reviewer/e40adafa23250fdd5024c9887544317a1101534d"
        )
        assert response.status_code == 403

    def test_reviewer_session_with_non_reviewer_returns_403(self, client):
        """Session user_id pointing to a non-reviewer should return 403."""
        _login_session(client, "e40adafa23250fdd5024c9887544317a1101534d")
        response = client.get("/reviewer")
        assert response.status_code == 403

    def test_reviewer_stale_session_returns_401(self, client):
        """Session with a user_id that no longer exists should return 401."""
        _login_session(client, "deleted-user-that-does-not-exist")
        response = client.get("/reviewer")
        assert response.status_code == 401

    def test_htmx_401_returns_hx_redirect(self, client):
        """HTMX request hitting 401 should get HX-Redirect for recovery."""
        response = client.get("/reviewer", headers={"HX-Request": "true"})
        assert response.status_code == 401
        assert "HX-Redirect" in response.headers

    def test_htmx_403_returns_hx_redirect(self, client):
        """HTMX request hitting 403 should get HX-Redirect for recovery."""
        response = client.get(
            "/reviewer/nonexistent-user-id",
            headers={"HX-Request": "true"},
        )
        assert response.status_code == 403
        assert "HX-Redirect" in response.headers

    def test_reviewer_redirects_to_default_filters(self, client):
        """GET /reviewer without filter params should redirect with defaults."""
        _login_session(client)
        response = client.get("/reviewer")
        assert response.status_code == 302
        assert "statusInput=offen" in response.headers["Location"]
        assert "sort_order=id_desc" in response.headers["Location"]


# ---------------------------------------------------------------------------
# Date type filter
# ---------------------------------------------------------------------------


class TestDateTypeFilter:
    """Verify that dateType toggles between dat_fund_von and dat_meld."""

    def test_date_filter_fund_default(self, client):
        """Default dateType=fund should filter on dat_fund_von (2024 dates)."""
        _login_session(client)
        response = client.get(
            "/reviewer?statusInput=all&sort_order=id_desc"
            "&dateFrom=01.10.2024&dateTo=31.12.2024&dateType=fund",
            follow_redirects=True,
        )
        assert response.status_code == 200
        # Reports with dat_fund_von in Oct-Dec 2024 exist in test data
        assert b"0 - 0 von 0" not in response.data

    def test_date_filter_fund_excludes_2025(self, client):
        """dateType=fund with 2025 range should return 0 results (no sightings in 2025)."""
        _login_session(client)
        response = client.get(
            "/reviewer?statusInput=all&sort_order=id_desc"
            "&dateFrom=01.01.2025&dateTo=28.02.2025&dateType=fund",
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"0 - 0 von 0" in response.data

    def test_date_filter_meld_finds_feb_2025(self, client):
        """dateType=meld with Feb 2025 range should find reports (all dat_meld in Feb 2025)."""
        _login_session(client)
        response = client.get(
            "/reviewer?statusInput=all&sort_order=id_desc"
            "&dateFrom=01.02.2025&dateTo=28.02.2025&dateType=meld",
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"0 - 0 von 0" not in response.data

    def test_date_filter_meld_excludes_2024(self, client):
        """dateType=meld with 2024 range should return 0 results (no reports filed in 2024)."""
        _login_session(client)
        response = client.get(
            "/reviewer?statusInput=all&sort_order=id_desc"
            "&dateFrom=01.01.2024&dateTo=31.12.2024&dateType=meld",
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"0 - 0 von 0" in response.data

    def test_date_type_preserved_in_html(self, client):
        """The dateType value should be present in the rendered HTML."""
        _login_session(client)
        response = client.get(
            "/reviewer?statusInput=all&sort_order=id_desc&dateType=meld",
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b'value="meld"' in response.data

    def test_date_type_defaults_to_fund(self, client):
        """Without explicit dateType, the default should be 'fund'."""
        _login_session(client)
        response = client.get(
            "/reviewer?statusInput=all&sort_order=id_desc",
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b'value="fund"' in response.data

    def test_date_filter_without_dates_shows_all(self, client):
        """When no date range is set, all reports should appear regardless of dateType."""
        _login_session(client)

        resp_fund = client.get(
            "/reviewer?statusInput=all&sort_order=id_desc&dateType=fund",
            follow_redirects=True,
        )
        resp_meld = client.get(
            "/reviewer?statusInput=all&sort_order=id_desc&dateType=meld",
            follow_redirects=True,
        )
        assert resp_fund.status_code == 200
        assert resp_meld.status_code == 200
        # Both should show the same total when no date filter is applied
        assert b"0 - 0 von 0" not in resp_fund.data
        assert b"0 - 0 von 0" not in resp_meld.data

    def test_date_filter_from_only(self, client):
        """dateFrom without dateTo should filter as open-ended range."""
        _login_session(client)
        response = client.get(
            "/reviewer?statusInput=all&sort_order=id_desc"
            "&dateFrom=01.12.2024&dateType=fund",
            follow_redirects=True,
        )
        assert response.status_code == 200
        # Reports 8,18,19 have dat_fund_von >= 2024-12-23
        assert b"0 - 0 von 0" not in response.data

    def test_date_filter_to_only(self, client):
        """dateTo without dateFrom should filter as open-ended range."""
        _login_session(client)
        response = client.get(
            "/reviewer?statusInput=all&sort_order=id_desc"
            "&dateTo=15.01.2024&dateType=fund",
            follow_redirects=True,
        )
        assert response.status_code == 200
        # Report 4 has dat_fund_von=2024-01-02
        assert b"0 - 0 von 0" not in response.data

    @pytest.mark.parametrize("bad_date", ["not-a-date", "2024-13-01", "abc"])
    def test_invalid_date_returns_empty(self, client, bad_date):
        """Malformed dates should return 0 results, not a server error."""
        _login_session(client)
        response = client.get(
            f"/reviewer?statusInput=all&sort_order=id_desc"
            f"&dateFrom={bad_date}&dateTo=28.02.2025&dateType=fund",
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"0 - 0 von 0" in response.data

    @pytest.mark.parametrize("bad_date", ["not-a-date", "32.13.2024"])
    def test_invalid_date_from_only_returns_empty(self, client, bad_date):
        """Malformed dateFrom alone should return 0 results."""
        _login_session(client)
        response = client.get(
            f"/reviewer?statusInput=all&sort_order=id_desc"
            f"&dateFrom={bad_date}&dateType=fund",
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"0 - 0 von 0" in response.data

    @pytest.mark.parametrize("bad_date", ["not-a-date", "32.13.2024"])
    def test_invalid_date_to_only_returns_empty(self, client, bad_date):
        """Malformed dateTo alone should return 0 results."""
        _login_session(client)
        response = client.get(
            f"/reviewer?statusInput=all&sort_order=id_desc"
            f"&dateTo={bad_date}&dateType=fund",
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"0 - 0 von 0" in response.data
