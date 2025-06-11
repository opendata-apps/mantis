import pytest
from unittest.mock import patch
from app.routes.statistics import stats_bardiagram_datum


@pytest.mark.parametrize("dbfields,page,marker,expected_x,expected_y", [
    (
        ['dat_fund_von'],
        'stats-meld-fund.html',
        'meldungen_meld_fund',
        ['2024-01-20', '2024-01-28', '2024-02-12', '2024-02-19'],
        [1, 1, 1, 1]
    ),
    # Add more parameter sets as needed for other test cases
])
@pytest.mark.usefixtures("session_with_user", "request_context")
def test_stats_bardiagram(mock_request, session, dbfields, page, marker, expected_x, expected_y):
    """Parameterized test for stats_bardiagram_datum with different configurations."""

    # Setup date range in the form data
    mock_request.form = {
        'dateFrom': '2024-01-07',
        'dateTo': '2024-03-06',
        'user_id': '9999'
    }

    with patch('app.routes.statistics.render_template') as mock_render_template:
        # Set mock return value
        mock_render_template.return_value = None

        # Call the function
        stats_bardiagram_datum(
            request=mock_request,
            dbfields=dbfields,
            page=page,
            marker=marker,
            dateFrom='2024-01-07',
            dateTo='2024-03-06'
        )

        # Check only trace1 (graph values)
        mock_render_template.assert_called_once()
        actual_values = mock_render_template.call_args[1]['trace1']

        expected_values = {
            'x': expected_x,
            'y': expected_y
        }

        assert actual_values == expected_values, \
            f"Expected values: {expected_values}, but got: {actual_values}"
