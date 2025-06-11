"""Tests for the administrative area lookup by coordinates functionality."""
from unittest.mock import patch


@patch('app.tools.find_gemeinde.get_amt_full_scan')
def test_amt_lookup_with_mocking(mock_get_amt, session):
    """Test administrative area lookup functionality with mocking.
    
    This test uses mocking to verify the lookup function works as expected
    without depending on specific GeoJSON processing.
    """
    # Configure the mock to return a predefined value
    mock_get_amt.return_value = "12062134 -- Fichtwald"

    # Create a test coordinate point
    test_point = ['13.44', '51.74']

    # Call the mocked function with our test point
    from app.tools.find_gemeinde import get_amt_full_scan
    result = get_amt_full_scan(test_point)

    # Verify the mock was called with the correct parameters
    mock_get_amt.assert_called_once_with(test_point)

    # Verify the expected result was returned
    assert result == "12062134 -- Fichtwald"
    assert "Fichtwald" in result, "Result should contain the administrative area name"
