"""Place-name normalization for coordinate grading."""

import re

_UMLAUTS = str.maketrans({"ä": "a", "ö": "o", "ü": "u", "ß": "ss"})
_SEPARATORS = re.compile(r"[^a-z0-9]+")


def normalize_place_name(value: str) -> str:
    """Casefold, drop umlaut diacritics, and strip all non-alphanumerics.

    Diacritics collapse to the base vowel (ü→u) so an ASCII-typed "Lubbenau"
    matches the reference "Lübbenau"; ß→ss is the only multi-char fold.
    Separators (spaces, hyphens, dots) are then removed so "Sachsen Anhalt",
    "Sachsen-Anhalt", and "Sachsen–Anhalt" all normalize alike.
    """
    folded = (value or "").casefold().translate(_UMLAUTS)
    return _SEPARATORS.sub("", folded)


# Shortest place name allowed to match purely as an affix of a longer one. Guards
# against stray short fragments ("Aue", "BER") while admitting real German compound
# Ortsteile ("Teutschenthal" is a suffix of "Unterteutschenthal"); the shortest base
# we rely on is "Kyhna" (5).
_MIN_AFFIX_LEN = 5


def names_match_norm(stored: str, resolved: str) -> bool:
    """Lenient place-name match: separator-insensitive equality OR a long shared affix.

    After normalization, matches when the two forms are equal (so "Klein Schauen" ==
    "Kleinschauen", "Sachsen Anhalt" == "Sachsen-Anhalt") or when the shorter name is
    a prefix/suffix of the longer one and is at least _MIN_AFFIX_LEN chars — covering
    German compound Ortsteile ("Teutschenthal" ⊏ "Unterteutschenthal", "Belzig" ⊏ "Bad
    Belzig", "Berlin" ⊏ "Berlin-Mitte"). Requiring an *affix* (not any substring) plus
    a length floor rejects false positives like "Aue" inside "Blaue Berge", "BER"
    inside "Rotberg", or "Linde" inside "Berlin-Lindenberg".
    """
    a = normalize_place_name(stored)
    b = normalize_place_name(resolved)
    if not a or not b:
        return False
    if a == b:
        return True
    short, long = (a, b) if len(a) <= len(b) else (b, a)
    return len(short) >= _MIN_AFFIX_LEN and (
        long.startswith(short) or long.endswith(short)
    )
