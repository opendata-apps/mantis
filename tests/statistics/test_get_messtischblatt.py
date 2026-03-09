import pytest
from app.tools.mtb_calc import get_mtb


@pytest.mark.parametrize(
    "lat,lon,expected_mtb",
    [
        (51.738052, 13.440228, "4246"),  # Trebbin - verified
        (52.520008, 13.404954, "3446"),  # Berlin - corrected
        (52.390569, 13.064473, "3544"),  # Potsdam - corrected
        (51.339695, 12.373075, "4640"),  # Leipzig - corrected
        (51.050407, 13.737262, "4948"),  # Dresden - corrected
    ],
)
def test_get_mtb_for_various_locations(lat, lon, expected_mtb, session):
    """Test MTB calculation for various locations in Germany."""
    mtb = get_mtb(lat, lon)
    assert mtb == expected_mtb, (
        f"MTB for lat={lat}, lon={lon} should be {expected_mtb}, got {mtb}"
    )


def test_get_mtb_with_edge_coordinates(session):
    """Test MTB calculation with coordinates at grid boundaries."""
    # Test coordinates exactly on grid boundaries
    mtb = get_mtb(52.0, 13.0)
    assert mtb is not None, "Should handle coordinates on grid boundaries"


@pytest.mark.parametrize(
    "lat,lon,expected_mtb",
    [
        # Boundary case: lat just north of a 6-minute row boundary.
        # Row 48 south edge is at startbreite - 48 * 0.1 = 51.07688.
        # 51.077 is just north of that edge -> should be row 48, col 44.
        (51.077, 13.0, "4844"),
        # Another boundary: 51.17688 is the row 47 south edge.
        # 51.177 is just north -> row 47.
        (51.177, 13.0, "4744"),
        # Longitude boundary: 10-minute column edges.
        # Col 44 west edge at 6.0 + 42 * (10/60) = 13.0.
        # 13.001 is just east -> col 44.
        (52.0, 13.001, "3944"),
    ],
)
def test_get_mtb_boundary_precision(lat, lon, expected_mtb, session):
    """Test MTB precision near 6-minute row boundaries.

    The calculation must use full decimal-degree precision, not truncate
    to integer minutes, to avoid off-by-one errors at tile boundaries.
    """
    mtb = get_mtb(lat, lon)
    assert mtb == expected_mtb, (
        f"MTB for lat={lat}, lon={lon} should be {expected_mtb}, got {mtb}"
    )
