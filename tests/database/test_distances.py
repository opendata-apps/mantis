"""Tests for distance calculation functionality.

Mocks the Nominatim geocoding API to avoid live HTTP calls during testing.
Coordinates below were captured from real Nominatim responses and pinned so
tests are fast, deterministic, and network-independent.
"""

from unittest.mock import Mock, patch

import pytest

from app.tools.check_distance import calculate_distance, get_coordinates_from_address

# Realistic coordinates captured from Nominatim for each test address.
# Keyed by city name for easy lookup in the mock.
_NOMINATIM_RESPONSES = {
    "Caputh": {"lat": "52.350200", "lon": "12.997500"},
    "Berlin": {"lat": "52.517030", "lon": "13.388820"},
    "Potsdam": {"lat": "52.394500", "lon": "13.061200"},
}


def _mock_nominatim_get(url, params=None, headers=None, **kwargs):
    """Return canned Nominatim responses based on the query city."""
    query = params.get("q", "") if params else ""
    for city, coords in _NOMINATIM_RESPONSES.items():
        if city in query:
            resp = Mock()
            resp.status_code = 200
            resp.json.return_value = [coords]
            return resp
    # Unknown address — return empty result
    resp = Mock()
    resp.status_code = 200
    resp.json.return_value = []
    return resp


@pytest.mark.parametrize(
    "address_data,expected_min_distance",
    [
        (
            {
                "id": 11,
                "plz": "14548",
                "city": "Caputh",
                "street": "Schmerberger Weg 92a",
                "housenumber": None,
                "marker": ["51.464414", "13.540649"],
            },
            10.0,
        ),
        (
            {
                "id": 12,
                "plz": "10117",
                "city": "Berlin",
                "street": "Unter den Linden",
                "housenumber": "1",
                "marker": ["52.516275", "13.388889"],
            },
            0.0,  # Same location
        ),
        (
            {
                "id": 13,
                "plz": "14467",
                "city": "Potsdam",
                "street": "Breite Straße",
                "housenumber": "1",
                "marker": [
                    "52.520008",  # Berlin coordinates
                    "13.404954",
                ],
            },
            20.0,  # Different city
        ),
    ],
)
@patch(
    "app.tools.check_distance.requests.get",
    side_effect=_mock_nominatim_get,
)
def test_distance_calculation(mock_get, address_data, expected_min_distance):
    """Test the distance calculation between geocoded address and provided coordinates.

    Verifies that:
    1. get_coordinates_from_address correctly parses the mocked API response
    2. calculate_distance returns a sensible geodesic distance
    3. The calculated distance exceeds the expected minimum
    """
    coord1 = get_coordinates_from_address(
        address_data["street"],
        address_data["city"],
        address_data["plz"],
        address_data["housenumber"],
    )

    coord2 = address_data["marker"]

    assert coord1 is not None, "Geocoding returned None — check mock data"
    distance = calculate_distance(coord1, coord2)
    assert distance > expected_min_distance, (
        f"Distance {distance:.2f}km should be greater than {expected_min_distance}km"
    )


@patch(
    "app.tools.check_distance.requests.get",
    side_effect=_mock_nominatim_get,
)
def test_geocode_unknown_address_returns_none(mock_get):
    """get_coordinates_from_address returns None for unknown addresses."""
    result = get_coordinates_from_address("Nonexistent Street", "Atlantis", "00000")
    assert result is None


@patch("app.tools.check_distance.requests.get")
def test_geocode_api_error_returns_none(mock_get):
    """get_coordinates_from_address returns None on HTTP errors."""
    mock_get.return_value = Mock(status_code=500)
    result = get_coordinates_from_address("Breite Straße", "Potsdam", "14467")
    assert result is None
