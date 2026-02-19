import pytest
from unittest.mock import patch
from flask import session as flask_session
from app.routes.statistics import stats_geschlecht


@pytest.mark.usefixtures("session_with_user", "request_context")
def test_stats_geschlecht(session):
    """Test zur Prüfung der Statistik nach Geschlecht/Entwicklungsstadien."""

    flask_session["date_from"] = "2024-01-01"
    flask_session["date_to"] = "2025-12-31"
    flask_session["ags"] = ""

    with patch("app.routes.statistics.render_template") as mock_render_template:
        mock_render_template.return_value = None

        stats_geschlecht(marker="geschlecht")

        mock_render_template.assert_called_once()

        actual_values = mock_render_template.call_args[1]["values"]

        expected_keys = {
            "Männchen",
            "Weibchen",
            "Nymphen",
            "Ootheken",
            "Andere",
            "Gesamt",
        }
        assert set(actual_values.keys()) == expected_keys, (
            f"Expected keys: {expected_keys}, but got: {set(actual_values.keys())}"
        )

        for key, value in actual_values.items():
            assert isinstance(value, int) and value >= 0, (
                f"Value for {key} should be a non-negative integer, but got: {value}"
            )

        assert sum(actual_values.values()) > 0, (
            "Should have at least some sightings in the test data"
        )
