"""The one German postal code check the app applies.

It mirrors the database's ``plz ~ '^[0-9]{5}$'``;
``tests/unit/test_postal_code.py`` holds the two against each other.
"""

import re

# [0-9] rather than \d: \d also matches ٠١٢٣٤ and ０１２３４. No anchors either —
# Python's $ still matches before a trailing newline where Postgres' does not,
# so "12345\n" would pass here and then fail the CHECK constraint.
_PLZ = re.compile(r"[0-9]{5}")


def is_valid_plz(value: object) -> bool:
    """True for exactly five ASCII digits; leading zeros belong to the code."""
    return isinstance(value, str) and _PLZ.fullmatch(value) is not None
