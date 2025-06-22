import pytest
from app.tools.mtb_calc import get_mtb


@pytest.mark.parametrize("lat,lon,expected_mtb", [
    (51.738052, 13.440228, "4246"),  # Trebbin - verified
    (52.520008, 13.404954, "3446"),  # Berlin - corrected
    (52.390569, 13.064473, "3544"),  # Potsdam - corrected
    (51.339695, 12.373075, "4640"),  # Leipzig - corrected
    (51.050407, 13.737262, "4948"),  # Dresden - corrected
])
def test_get_mtb_for_various_locations(lat, lon, expected_mtb, session):
    """Test MTB calculation for various locations in Germany."""
    mtb = get_mtb(lat, lon)
    assert mtb == expected_mtb, f"MTB for lat={lat}, lon={lon} should be {expected_mtb}, got {mtb}"


def test_get_mtb_with_edge_coordinates(session):
    """Test MTB calculation with coordinates at grid boundaries."""
    # Test coordinates exactly on grid boundaries
    mtb = get_mtb(52.0, 13.0)
    assert mtb is not None, "Should handle coordinates on grid boundaries"
