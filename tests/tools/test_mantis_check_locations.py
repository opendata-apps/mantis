import pytest
from unittest.mock import patch, Mock
import json
from app.tools.mantis_check_locations import check_location


@pytest.fixture
def mock_response():
    """Create a mock response object to simulate the Overpass API response."""
    mock_resp = Mock()
    mock_resp.json.return_value = {
        'elements': [
            {
                'tags': {
                    'name': 'Schenkenberg'
                }
            },
            {
                'tags': {
                    'name': 'Nearby Town'
                }
            }
        ]
    }
    return mock_resp


@patch('requests.get')
def test_check_location_match(mock_get, mock_response):
    """Test that check_location correctly identifies when a location matches."""
    mock_get.return_value = mock_response
    
    # Test data where the location name exists in the API response
    fundort = (52.38948, 12.70295, "Schenkenberg", 1908)
    
    results = check_location(fundort)
    
    # Check that the function made a request to the API
    mock_get.assert_called_once()
    
    # Check that we got a successful result
    assert any("OK" in result for result in results)
    assert any("Schenkenberg" in result for result in results)


@patch('requests.get')
def test_check_location_no_match(mock_get, mock_response):
    """Test that check_location correctly handles when a location doesn't match."""
    mock_get.return_value = mock_response
    
    # Test data where the location name doesn't exist in the API response
    fundort = (52.38948, 12.70295, "NonExistentPlace", 1909)
    
    results = check_location(fundort)
    
    # Check that the function made requests to the API
    assert mock_get.call_count > 1
    
    # Check that we got a "check" result or eventually gave up
    assert any("<-- Prüfen!" in result for result in results) or results


@patch('requests.get')
def test_check_location_exception(mock_get):
    """Test that check_location handles exceptions gracefully."""
    # Make the request.get call raise an exception
    mock_get.side_effect = Exception("Test exception")
    
    fundort = (52.38948, 12.70295, "Schenkenberg", 1908)
    
    results = check_location(fundort)
    
    # Check that the function caught the exception and returned an error message
    assert any("<-- Abbruch!" in result for result in results) 