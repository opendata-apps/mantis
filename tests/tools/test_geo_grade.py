from app.tools.geo_grade import grade_location
from app.tools.geo_names import NearestPlace


# stub finders -----------------------------------------------------------
def amt(land, gen, kreis, ags=12062264):
    return lambda pt: {"land": land, "gen": gen, "kreis": kreis, "ags": ags}


def no_amt(pt):
    return None


def place(name, dist, ags=12062264):
    return lambda pt: [NearestPlace(name=name, ags=ags, kreis="K", distance_m=dist)]


def places(*specs):
    """specs: (name, dist) tuples -> sorted-by-distance candidate list."""
    items = sorted(
        (NearestPlace(name=n, ags=12062264, kreis="K", distance_m=d) for n, d in specs),
        key=lambda p: p.distance_m,
    )
    return lambda pt: items


def no_place(pt):
    return []


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


def test_ortsteil_not_shadowed_by_closer_other_place():
    # The absolute-nearest place is a differently-named point (Elstal's Olympic
    # Village) but the typed Ortsteil also lies in range — must still be ORTSTEIL.
    g = grade_location(
        52.526,
        13.005,
        "Brandenburg",
        "Havelland",
        "Elstal",
        find_amt=amt("Brandenburg", "Wustermark", "Havelland"),
        nearest_place=places(("Olympisches Dorf", 1353), ("Elstal", 1620)),
    )
    assert g.matched_level == "ORTSTEIL" and g.grade == "HIGH"


def test_ortsteil_within_bumped_cap():
    # Saarmund's GN250 centroid is 2050 m from the pin — inside the 3 km cap.
    g = grade_location(
        52.308,
        13.103,
        "Brandenburg",
        "Potsdam-Mittelmark",
        "Saarmund",
        find_amt=amt("Brandenburg", "Nuthetal", "Potsdam-Mittelmark"),
        nearest_place=place("Saarmund", 2050),
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


def test_city_state_ort_matches_land_is_high():
    # Pin resolves to a Berlin Bezirk (gen='Mitte'); typed ort 'Berlin' names the
    # city-state and the pin is really in Berlin -> GEMEINDE/HIGH, not LOW.
    g = grade_location(
        52.52,
        13.40,
        "Berlin",
        "Berlin",
        "Berlin",
        find_amt=amt("Berlin", "Mitte", "Berlin", ags=11000000),
        nearest_place=place("Alexanderplatz", 300, ags=99999999),
    )
    assert g.matched_level == "GEMEINDE" and g.grade == "HIGH"


def test_wrong_pin_typed_city_state_stays_low():
    # Typed 'Berlin' but the pin is actually in Brandenburg: the rule keys off the
    # resolved Land (Brandenburg, not a city-state) so it must NOT be promoted.
    g = grade_location(
        52.4,
        13.0,
        "Berlin",
        "Berlin",
        "Berlin",
        find_amt=amt("Brandenburg", "Eichwalde", "Dahme-Spreewald", ags=12061),
        nearest_place=place("Eichwalde", 200, ags=99999999),
    )
    assert g.grade == "LOW"
