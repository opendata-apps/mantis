from app.tools.geo_grade import grade_location
from app.tools.geo_names import NearestPlace


# stub finders -----------------------------------------------------------
def amt(land, gen, kreis, ags=12062264):
    return lambda pt: {"land": land, "gen": gen, "kreis": kreis, "ags": ags}


def no_amt(pt):
    return None


def place(name, dist, ags=12062264):
    return lambda pt: NearestPlace(name=name, ags=ags, kreis="K", distance_m=dist)


def no_place(pt):
    return None


def test_outside_de_is_low():
    g = grade_location(
        51.0,
        14.7,
        "Woiwodschaft Lebus",
        None,
        "Słubice",
        find_amt=no_amt,
        nearest_place=no_place,
    )
    assert g.matched_level == "OUTSIDE_DE" and g.grade == "LOW"


def test_ortsteil_match_is_high_schadewitz_regression():
    g = grade_location(
        51.58,
        13.52,
        "Brandenburg",
        "Elbe-Elster",
        "Schadewitz",
        find_amt=amt("Brandenburg", "Schönborn", "Elbe-Elster"),
        nearest_place=place("Schadewitz", 120),
    )
    assert g.matched_level == "ORTSTEIL" and g.grade == "HIGH"


def test_gemeinde_name_match_is_high():
    g = grade_location(
        51.6,
        13.55,
        "Brandenburg",
        "Elbe-Elster",
        "Schönborn",
        find_amt=amt("Brandenburg", "Schönborn", "Elbe-Elster"),
        nearest_place=place("Faraway", 9000, ags=99999999),
    )
    assert g.matched_level == "GEMEINDE" and g.grade == "HIGH"


def test_kreis_match_only_is_medium():
    g = grade_location(
        51.6,
        13.55,
        "Brandenburg",
        "Elbe-Elster",
        "Wrongplace",
        find_amt=amt("Brandenburg", "Schönborn", "Elbe-Elster"),
        nearest_place=place("Faraway", 9000, ags=99999999),
    )
    assert g.matched_level == "KREIS" and g.grade == "MEDIUM"


def test_land_mismatch_is_low():
    g = grade_location(
        52.5,
        13.4,
        "Brandenburg",
        "Spree-Neiße",
        "Anything",
        find_amt=amt("Berlin", "Treptow-Köpenick", "Berlin", ags=11000000),
        nearest_place=place("Faraway", 9000, ags=99999999),
    )
    assert g.matched_level in ("LAND", "NONE") and g.grade == "LOW"
