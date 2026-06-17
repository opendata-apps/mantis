from app.tools.normalize_text import names_match_norm, normalize_place_name


def test_normalize_folds_umlauts_and_strips_separators():
    assert normalize_place_name(" Schönborn ") == "schonborn"
    assert normalize_place_name("Lübbenau/Spreewald") == "lubbenauspreewald"
    assert normalize_place_name("Sachsen-Anhalt") == "sachsenanhalt"


def test_names_match_norm_bidirectional_and_umlaut_insensitive():
    assert names_match_norm("Berlin-Mitte", "Berlin")
    assert names_match_norm("Lubbenau", "Lübbenau/Spreewald")
    assert not names_match_norm("München", "Hamburg")
    assert not names_match_norm("", "Berlin")


def test_names_match_norm_ignores_separator_style():
    # Same name, different separators: space vs hyphen must match.
    assert names_match_norm("Sachsen Anhalt", "Sachsen-Anhalt")
    assert names_match_norm("Berlin Mitte", "Berlin-Mitte")


def test_names_match_norm_affix_containment():
    # The shorter name is a prefix/suffix of the longer one -> match.
    assert names_match_norm("Frankfurt", "Frankfurt (Oder)")
    assert names_match_norm("Köpenick", "Berlin-Köpenick")
    assert names_match_norm("Bad Belzig", "Belzig")
    # Spacing differs but the stripped forms are equal -> still match.
    assert names_match_norm("Klein Schauen", "Kleinschauen")


def test_names_match_norm_german_compound_ortsteile():
    # Ober-/Unter-/Nieder-/Alt-/Neu- compounds must match their base name (the base
    # is a suffix of the compound). These are single-word, so token splitting fails.
    assert names_match_norm("Unterteutschenthal", "Teutschenthal")
    assert names_match_norm("Altbensdorf", "Bensdorf")
    assert names_match_norm("Niederhadamar", "Hadamar")
    # Abbreviation that is a clean prefix still matches.
    assert names_match_norm("Münster (Hess.)", "Münster (Hessen)")


def test_names_match_norm_rejects_short_substring_false_positives():
    # Short fragments and mid-word substrings (not affixes) must NOT match.
    assert not names_match_norm("Aue", "Blaue Berge")
    assert not names_match_norm("Au", "Augustusburg")
    assert not names_match_norm("Elm", "Elmshorn")
    assert not names_match_norm("Linde", "Berlin-Lindenberg")
    assert not names_match_norm("BER", "Rotberg")
