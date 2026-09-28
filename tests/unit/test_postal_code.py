"""The postal code rule, and proof that Python and Postgres agree on it.

Four call sites used to carry their own version. The form's ``\\d{5}`` accepted
Unicode decimals the other three rejected, so a code in Arabic-Indic digits
passed validation and then failed the CHECK constraint on save. The
equivalence test below is what keeps the remaining two implementations — this
module and the ``plz_format`` CHECK constraint — from drifting apart again.
"""

import pytest
from sqlalchemy import text

from app.database.fundorte import TblFundorte
from app.tools.postal_code import is_valid_plz

# Both the plausible and the awkward: leading zero (Dresden), Arabic-Indic and
# fullwidth digits, and the separators a phone keyboard slips in.
CANDIDATES = [
    "12345",
    "01067",
    "00000",
    "99999",
    "1234",
    "123456",
    "",
    " 1234",
    "1234 ",
    "12 34",
    "12.34",
    "abcde",
    "1234a",
    "٠١٢٣٤",
    "１２３４５",
    "12\n34",
    "12345\n",
]


@pytest.mark.parametrize("value", CANDIDATES)
def test_python_and_check_constraint_agree(session, value):
    """Run each candidate through the exact SQL the table is created with."""
    constraint = next(
        c
        for c in TblFundorte.__table__.constraints
        if c.name == "ck_fundorte_plz_format"
    )
    # "plz ~ '...'" with the column swapped for a bound parameter.
    condition = str(constraint.sqltext).replace("plz", ":value", 1)

    accepted_by_db = session.scalar(text(f"SELECT {condition}"), {"value": value})

    assert is_valid_plz(value) == accepted_by_db, (
        f"{value!r}: Python says {is_valid_plz(value)}, Postgres says {accepted_by_db}"
    )


def test_arabic_indic_digits_are_refused():
    """The regression itself: \\d would match these, [0-9] does not."""
    assert not is_valid_plz("٠١٢٣٤")


def test_leading_zero_survives():
    assert is_valid_plz("01067")


def test_non_string_input_is_refused():
    assert not is_valid_plz(None)
    assert not is_valid_plz(12345)
