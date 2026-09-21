"""Agreement between a typed address and the coordinate it claims to describe."""

# Wider than Germany's true extent (lat 47.27–55.06, lon 5.87–15.04): a pin on
# the border stays inside.
GERMANY_BBOX_LAT = (47.0, 55.3)
GERMANY_BBOX_LON = (5.5, 15.4)

# The 16 Bundesländer plus "Deutschland". Abbreviations ("NRW") are not matched.
GERMAN_LAND_NAMES = frozenset(
    {
        "baden-württemberg",
        "bayern",
        "berlin",
        "brandenburg",
        "bremen",
        "deutschland",
        "hamburg",
        "hessen",
        "mecklenburg-vorpommern",
        "niedersachsen",
        "nordrhein-westfalen",
        "rheinland-pfalz",
        "saarland",
        "sachsen",
        "sachsen-anhalt",
        "schleswig-holstein",
        "thüringen",
    }
)


def contradicts_german_land(latitude, longitude, land):
    """True if the point is nowhere near Germany but the reporter named a Bundesland.

    Bounding box and Land name only: a pin in the wrong Gemeinde passes.

    >>> contradicts_german_land(24.9, 24.9, "Baden-Württemberg")
    True
    >>> contradicts_german_land(48.9, 8.75, "Baden-Württemberg")
    False
    >>> contradicts_german_land(45.53, 10.55, "Lombardei")
    False
    """
    if latitude is None or longitude is None or not land:
        return False

    if land.strip().casefold() not in GERMAN_LAND_NAMES:
        return False

    return not (
        GERMANY_BBOX_LAT[0] <= latitude <= GERMANY_BBOX_LAT[1]
        and GERMANY_BBOX_LON[0] <= longitude <= GERMANY_BBOX_LON[1]
    )
