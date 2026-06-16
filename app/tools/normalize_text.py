"""Place-name normalization for coordinate grading."""

_UMLAUTS = str.maketrans({"ä": "a", "ö": "o", "ü": "u", "ß": "ss"})


def normalize_place_name(value: str) -> str:
    """Lowercase, trim, and drop German umlaut diacritics for lenient matching.

    Diacritics collapse to the base vowel (ü→u) so an ASCII-typed "Lubbenau"
    matches the reference "Lübbenau". ß→ss is the only multi-char fold.
    """
    return (value or "").strip().lower().translate(_UMLAUTS)


def names_match_norm(stored: str, resolved: str) -> bool:
    """Bidirectional substring match on normalized names."""
    a = normalize_place_name(stored)
    b = normalize_place_name(resolved)
    if not a or not b:
        return False
    return a in b or b in a
