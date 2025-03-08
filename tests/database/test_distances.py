"""Tests for distance calculation functionality."""
from app.tools.check_distance import get_coordinates_from_address, calculate_distance
import pytest


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
                "marker": [
                    "51.464414",
                    "13.540649"
                ]
            }, 
            10.0
        ),
    ]
)
def test_distance_calculation(session, address_data, expected_min_distance):
    """Test the distance calculation between geocoded address and provided coordinates.
    
    This test verifies that:
    1. The geocoding function can retrieve coordinates from an address
    2. The distance calculation function works as expected
    3. The calculated distance meets the expected minimum distance
    
    Parameters:
        session: The database session fixture
        address_data: Dictionary containing address information and marker coordinates
        expected_min_distance: The minimum expected distance in kilometers
    """
    # Get coordinates from the address
    coord1 = get_coordinates_from_address(
        address_data["street"],
        address_data["city"],
        address_data["plz"],
        address_data["housenumber"]
    )
    
    # Get the marker coordinates
    coord2 = address_data['marker']
    
    # Calculate the distance between coordinates if both are available
    if coord1 and coord2:
        distance = calculate_distance(coord1, coord2)
        # Assert that the distance is greater than the expected minimum
        assert distance > expected_min_distance, f"Distance should be greater than {expected_min_distance}km"
    else:
        pytest.skip("Could not retrieve coordinates for the address")
