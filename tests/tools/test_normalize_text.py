from app.tools.normalize_text import names_match_norm, normalize_place_name


def test_normalize_folds_umlauts_and_case():
    assert normalize_place_name(" Schönborn ") == "schonborn"
    assert normalize_place_name("Lübbenau/Spreewald") == "lubbenau/spreewald"


def test_names_match_norm_bidirectional_and_umlaut_insensitive():
    assert names_match_norm("Berlin-Mitte", "Berlin")
    assert names_match_norm("Lubbenau", "Lübbenau/Spreewald")
    assert not names_match_norm("München", "Hamburg")
    assert not names_match_norm("", "Berlin")
