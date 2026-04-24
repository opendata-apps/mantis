"""End-to-end tests for the reviewer-only statistics blueprint.

``stats_start`` is a dispatcher that reads ``stats`` from the POST body
and hands off to one of ~12 branches. Previously only a handful of
branches were covered, leaving ``stats_amt``, ``stats_gesamt``,
``stats_feedback``, ``stats_mtb``, and the three date-based variants
untested.

These tests go through the Flask test client with an authenticated
reviewer session so the ``reviewer_required`` decorator + the match
dispatch + the downstream query + the Jinja template all run — catching
regressions at each layer at once.
"""

import pytest


@pytest.fixture
def reviewer_client(authenticated_client):
    """Shorthand — ``authenticated_client`` already has ``user_id=9999``
    in the session, which maps to the seeded reviewer."""
    return authenticated_client


class TestStatsDispatchSmoke:
    """Each branch of the ``match`` block maps to a specific template.
    Asserting the template name catches dispatch-table mistakes that a
    plain 200-status check would miss (e.g. two branches pointing at
    the same template, or a branch renamed but the dispatcher wasn't
    updated)."""

    # Branch → expected Jinja template. Confirmed via render_template spy.
    DISPATCH = {
        "start": "statistics/statistiken.html",
        "geschlecht": "statistics/stats-geschlecht.html",
        "meldungen_meldedatum": "statistics/stats-meldedatum.html",
        "meldungen_funddatum": "statistics/stats-funddatum.html",
        "meldungen_meld_fund": "statistics/stats-meld-fund.html",
        "meldungen_mtb": "statistics/stats-messtischblatt.html",
        "meldungen_amt": "statistics/stats-gemeinde.html",
        "meldungen_laender": "statistics/stats-laender.html",
        "meldungen_brb": "statistics/stats-bundesland.html",
        "meldungen_berlin": "statistics/stats-bundesland.html",
        "meldungen_gesamt": "statistics/stats-table-all.html",
        "meldungen_zeiten": "statistics/stats-daily-average.html",
        "feedback": "statistics/stats-feedback.html",
        # Unknown key → default case renders the menu (same as "start")
        "does-not-exist": "statistics/statistiken.html",
    }

    @pytest.mark.parametrize(
        ("stats_key", "expected_template"), sorted(DISPATCH.items())
    )
    def test_statistik_dispatch_renders_expected_template(
        self, reviewer_client, stats_key, expected_template
    ):
        from unittest.mock import patch

        from flask import render_template

        rendered = []

        def spy(name, **ctx):
            rendered.append(name)
            return render_template(name, **ctx)

        with patch("app.routes.statistics.render_template", side_effect=spy):
            response = reviewer_client.post(
                "/statistik",
                data={
                    "stats": stats_key,
                    "dateFrom": "2024-01-01",
                    "dateTo": "2026-12-31",
                    "ags": "",
                },
            )

        assert response.status_code == 200
        assert rendered == [expected_template], (
            f"branch {stats_key!r} should render {expected_template!r}, "
            f"got {rendered!r}"
        )

    def test_statistik_requires_reviewer_session(self, client):
        """Unauthenticated callers get 403 from ``reviewer_required``."""
        response = client.post("/statistik", data={"stats": "start"})
        assert response.status_code == 403

    def test_statistik_get_also_dispatches(self, reviewer_client):
        """``stats_start`` accepts both GET and POST; the GET path should
        fall through to ``start`` with session-default date range."""
        response = reviewer_client.get("/statistik")
        assert response.status_code == 200
        # The GET path must land on the menu template specifically
        assert b"menu" in response.data or b"Statistik" in response.data


class TestStatsAmt:
    """``stats_amt`` aggregates report counts per Amt/Gemeinde.

    The route is reached through the dispatcher; the template branch
    handles both "has results" (sets ``gemeinde`` from the first row)
    and "no results" (``fehler=True``).
    """

    def test_wide_range_has_results(self, reviewer_client):
        response = reviewer_client.post(
            "/statistik",
            data={
                "stats": "meldungen_amt",
                "dateFrom": "2024-01-01",
                "dateTo": "2026-12-31",
                "ags": "",
            },
        )
        assert response.status_code == 200

    def test_narrow_range_triggers_fehler_branch(self, reviewer_client):
        """A date range with no data must render the "no results" branch
        without raising. Guards against the index-0 access on an empty
        ``results`` list in ``stats_amt``."""
        response = reviewer_client.post(
            "/statistik",
            data={
                "stats": "meldungen_amt",
                "dateFrom": "1990-01-01",
                "dateTo": "1990-12-31",
                "ags": "",
            },
        )
        assert response.status_code == 200


class TestStatsGesamt:
    def test_gesamt_table_renders(self, reviewer_client):
        response = reviewer_client.post(
            "/statistik",
            data={
                "stats": "meldungen_gesamt",
                "dateFrom": "2024-01-01",
                "dateTo": "2026-12-31",
                "ags": "",
            },
        )
        assert response.status_code == 200


class TestStatsFeedback:
    def test_empty_feedback_renders(self, reviewer_client):
        response = reviewer_client.post(
            "/statistik",
            data={
                "stats": "feedback",
                "dateFrom": "2024-01-01",
                "dateTo": "2026-12-31",
            },
        )
        assert response.status_code == 200

    def test_feedback_aggregates_counts(self, reviewer_client, session):
        """Inserting a feedback row must surface through the aggregation
        without breaking the template."""
        from app.database.feedback_type import FeedbackSource
        from app.database.user_feedback import TblUserFeedback
        from app.database.users import TblUsers
        from sqlalchemy import select

        user = session.scalar(select(TblUsers).where(TblUsers.user_id == "9999"))
        session.add(
            TblUserFeedback(
                user_id=user.id,
                feedback_source=FeedbackSource.PRESS.value,
                source_detail="Tagesspiegel",
            )
        )
        session.flush()

        response = reviewer_client.post(
            "/statistik",
            data={
                "stats": "feedback",
                "dateFrom": "2024-01-01",
                "dateTo": "2026-12-31",
            },
        )
        assert response.status_code == 200
        assert b"Presse" in response.data or b"Tagesspiegel" in response.data


class TestStatsMtbTypeInput:
    """The ``typeInput`` form field selects which gender/stage column
    drives the circle counts. Exercising several values catches index
    mismatches between the parsed ``typeInput`` list and the SQL
    aggregation columns."""

    @pytest.mark.parametrize(
        "type_input", ["all", "maennlich", "weiblich", "oothek", "nymphe", "andere"]
    )
    def test_mtb_type_input_variants(self, reviewer_client, type_input):
        response = reviewer_client.post(
            "/statistik",
            data={
                "stats": "meldungen_mtb",
                "typeInput": type_input,
                "dateFrom": "2024-01-01",
                "dateTo": "2026-12-31",
                "ags": "",
            },
        )
        assert response.status_code == 200


class TestAutocompleteAgs:
    def test_short_query_returns_empty(self, client):
        """Typing a single character must short-circuit the DB query —
        avoids returning the whole ``aemter`` table."""
        response = client.get("/statistik/ags?ags_input=a")
        assert response.status_code == 200
        assert response.data == b""

    def test_empty_query_returns_empty(self, client):
        response = client.get("/statistik/ags?ags_input=")
        assert response.status_code == 200
        assert response.data == b""

    def test_long_query_returns_suggestions(self, client, session):
        """Inserting a fresh aemter row with a unique name must make
        that row discoverable through the autocomplete prefix query.

        We insert our own row (rather than relying on the fixture's
        four Lebusa/Fichtwald entries) because earlier tests — notably
        the ``flask seed-ags`` CLI test — may have replaced the seeded
        aemter within the shared session connection before the
        transaction rolls back."""
        from app.database.models import TblAemterCoordinaten

        sentinel = TblAemterCoordinaten(
            ags=99999001,
            gen="Teststadt-Suggest",
            properties={"type": "Point", "coordinates": [0, 0]},
        )
        session.add(sentinel)
        session.flush()

        response = client.get("/statistik/ags?ags_input=Testst")
        assert response.status_code == 200
        html = response.data.decode()
        assert html.count('class="suggestion"') == 1
        assert "Teststadt-Suggest" in html
        assert 'data-ags="99999001"' in html

    def test_prefix_matches_by_ags_too(self, client, session):
        """The query ORs name-prefix with AGS-prefix, so a numeric
        prefix of an existing AGS must also produce a hit — proving
        the OR branch (``cast(ags, String).startswith(q)``) is wired."""
        from app.database.models import TblAemterCoordinaten

        session.add(
            TblAemterCoordinaten(
                ags=88888777,
                gen="AgsMatchTest",
                properties={"type": "Point", "coordinates": [0, 0]},
            )
        )
        session.flush()

        response = client.get("/statistik/ags?ags_input=88888777")
        html = response.data.decode()
        assert response.status_code == 200
        assert 'data-ags="88888777"' in html
        assert "AgsMatchTest" in html
