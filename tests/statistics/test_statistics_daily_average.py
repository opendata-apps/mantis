import pytest
from unittest.mock import patch
from flask import session as flask_session
from app.routes.statistics import stats_daily_average


@pytest.mark.usefixtures("session_with_user", "request_context")
def test_stats_daily_average_returns_24_hours(session):
    """Test that stats_daily_average returns data for all 24 hours."""

    flask_session["date_from"] = "2024-01-01"
    flask_session["date_to"] = "2026-12-31"
    flask_session["ags"] = ""

    with patch("app.routes.statistics.render_template") as mock_render_template:
        mock_render_template.return_value = None

        stats_daily_average(marker="meldungen_zeiten")

        mock_render_template.assert_called_once()
        daten = mock_render_template.call_args[1]["daten"]

        assert len(daten) == 24, f"Expected 24 hours, got {len(daten)}"
        for h in range(24):
            key = str(h)
            assert key in daten, f"Missing hour {key}"
            assert isinstance(daten[key], int), f"Hour {key} value should be int"


@pytest.mark.usefixtures("session_with_user", "request_context")
def test_stats_daily_average_has_data_with_wide_range(session):
    """Test that the query returns actual counts with demo data."""

    flask_session["date_from"] = "2024-01-01"
    flask_session["date_to"] = "2026-12-31"
    flask_session["ags"] = ""

    with patch("app.routes.statistics.render_template") as mock_render_template:
        mock_render_template.return_value = None

        stats_daily_average(marker="meldungen_zeiten")

        daten = mock_render_template.call_args[1]["daten"]
        total = sum(daten.values())
        assert total > 0, "Should have at least some reports in demo data"


@pytest.mark.usefixtures("session_with_user", "request_context")
def test_stats_daily_average_empty_with_narrow_range(session):
    """Test that filtering by a range with no data returns all zeros."""

    flask_session["date_from"] = "1990-01-01"
    flask_session["date_to"] = "1990-12-31"
    flask_session["ags"] = ""

    with patch("app.routes.statistics.render_template") as mock_render_template:
        mock_render_template.return_value = None

        stats_daily_average(marker="meldungen_zeiten")

        daten = mock_render_template.call_args[1]["daten"]
        total = sum(daten.values())
        assert total == 0, "No reports should exist in 1990"


@pytest.mark.usefixtures("session_with_user", "request_context")
def test_stats_daily_average_ags_filter(session):
    """Test that AGS filter limits results to matching regions."""

    flask_session["date_from"] = "2024-01-01"
    flask_session["date_to"] = "2026-12-31"
    flask_session["ags"] = "99999"  # Non-existent AGS

    with patch("app.routes.statistics.render_template") as mock_render_template:
        mock_render_template.return_value = None

        stats_daily_average(marker="meldungen_zeiten")

        daten = mock_render_template.call_args[1]["daten"]
        total = sum(daten.values())
        assert total == 0, "Non-existent AGS should return no results"
