import pytest
from flask import session as flask_session
from unittest.mock import patch

from app.routes.statistics import stats_bundesland, stats_laender


@pytest.mark.usefixtures("session_with_user", "request_context")
def test_stats_laender_grouping_query_executes(form_with_dates, session):
    """Regression test: grouped state query must execute without PostgreSQL grouping errors."""

    flask_session["date_from"] = "2024-01-01"
    flask_session["date_to"] = "2026-12-31"
    flask_session["ags"] = ""

    with patch("app.routes.statistics.render_template") as mock_render_template:
        mock_render_template.return_value = None

        stats_laender(request=form_with_dates, marker="meldungen_laender")

        mock_render_template.assert_called_once()
        assert mock_render_template.call_args[0][0] == "statistics/stats-laender.html"
        assert isinstance(mock_render_template.call_args[1]["result"], dict)


@pytest.mark.parametrize(
    ("marker", "expected_template"),
    [
        ("meldungen_brb", "statistics/stats-bundesland.html"),
        ("meldungen_berlin", "statistics/stats-bundesland.html"),
    ],
)
@pytest.mark.usefixtures("session_with_user", "request_context")
def test_stats_bundesland_grouping_query_executes(
    form_with_dates, session, marker, expected_template
):
    """Regression test: district grouping query must execute without PostgreSQL grouping errors."""

    flask_session["date_from"] = "2024-01-01"
    flask_session["date_to"] = "2026-12-31"
    flask_session["ags"] = ""

    with patch("app.routes.statistics.render_template") as mock_render_template:
        mock_render_template.return_value = None

        stats_bundesland(request=form_with_dates, marker=marker)

        mock_render_template.assert_called_once()
        assert mock_render_template.call_args[0][0] == expected_template
        assert isinstance(mock_render_template.call_args[1]["result"], dict)
