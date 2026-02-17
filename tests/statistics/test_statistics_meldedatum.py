import pytest
from unittest.mock import patch
from flask import session as flask_session
from app.routes.statistics import stats_bardiagram_datum


@pytest.mark.parametrize(
    "dbfields,page,expected_x,expected_y",
    [
        (
            ["dat_fund_von"],
            "stats-meld-fund.html",
            ["2024-01-20", "2024-01-28", "2024-02-12", "2024-02-19"],
            [1, 1, 1, 1],
        ),
    ],
)
@pytest.mark.usefixtures("session_with_user", "request_context")
def test_stats_bardiagram(
    session, dbfields, page, expected_x, expected_y
):
    """Parameterized test for stats_bardiagram_datum with different configurations."""

    flask_session["date_from"] = "2024-01-07"
    flask_session["date_to"] = "2024-03-06"

    with patch("app.routes.statistics.render_template") as mock_render_template:
        mock_render_template.return_value = None

        stats_bardiagram_datum(
            dbfields=dbfields,
            page=page,
        )

        mock_render_template.assert_called_once()
        actual_values = mock_render_template.call_args[1]["trace1"]

        expected_values = {"x": expected_x, "y": expected_y}

        assert actual_values == expected_values, (
            f"Expected values: {expected_values}, but got: {actual_values}"
        )
