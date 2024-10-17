from app.tools.mantis_check_locations import check_location

def test_evaluate_location(client):
    """
    GIVEN a Location with longitude and latitude
    GIVEN a name for the place
    THEN check the distance between the place and the coordinates
    """
    locations = [
        [(52.37982, 13.2579, "Teltow", 378), '2600, Teltow, 378, OK\n']
    ]

    for location in locations:
        result = check_location(fundort=location[0])
        assert result[0] == location[1]

