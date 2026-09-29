"""Unit tests for pure helper functions in app/routes/report.py.

These tests exercise the helper functions directly — no Flask client or DB needed.
They catch regressions like the Männchen/Männlich mismatch that existed before.
"""

import pytest

from app.routes.report import (
    _format_coordinates,
    _format_date,
    _set_gender_fields,
)


# ---------------------------------------------------------------------------
# _set_gender_fields
# ---------------------------------------------------------------------------
class TestSetGenderFields:
    """Maps gender string → dict of DB column flags."""

    @pytest.mark.parametrize(
        "gender_value, expected",
        [
            ("Männlich", {"art_m": 1, "art_w": 0, "art_n": 0, "art_o": 0, "art_f": 0}),
            ("Weiblich", {"art_m": 0, "art_w": 1, "art_n": 0, "art_o": 0, "art_f": 0}),
            ("Nymphe", {"art_m": 0, "art_w": 0, "art_n": 1, "art_o": 0, "art_f": 0}),
            ("Oothek", {"art_m": 0, "art_w": 0, "art_n": 0, "art_o": 1, "art_f": 0}),
            ("Unbekannt", {"art_m": 0, "art_w": 0, "art_n": 0, "art_o": 0, "art_f": 0}),
            ("", {"art_m": 0, "art_w": 0, "art_n": 0, "art_o": 0, "art_f": 0}),
        ],
        ids=["male", "female", "nymph", "oothek", "unknown", "empty"],
    )
    def test_known_genders(self, gender_value, expected):
        assert _set_gender_fields(gender_value) == expected

    def test_exactly_one_flag_set_for_known_values(self):
        for value in ("Männlich", "Weiblich", "Nymphe", "Oothek"):
            result = _set_gender_fields(value)
            assert sum(result.values()) == 1, f"{value} should set exactly one flag"

    def test_unbekannt_sets_no_flags(self):
        result = _set_gender_fields("Unbekannt")
        assert sum(result.values()) == 0


# ---------------------------------------------------------------------------
# _format_date
# ---------------------------------------------------------------------------
class TestFormatDate:
    def test_valid_date(self):
        assert _format_date("2025-07-15") == "15.07.2025"

    def test_empty_string(self):
        assert _format_date("") == "-"

    def test_invalid_string(self):
        assert _format_date("not-a-date") == "not-a-date"

    def test_already_german_format(self):
        # Invalid for strptime("%Y-%m-%d"), returned as-is
        assert _format_date("15.07.2025") == "15.07.2025"


# ---------------------------------------------------------------------------
# _format_coordinates
# ---------------------------------------------------------------------------
class TestFormatCoordinates:
    def test_valid_pair(self):
        assert _format_coordinates("52.520008", "13.404954") == "52.520008, 13.404954"

    def test_six_decimal_places(self):
        result = _format_coordinates("52.5", "13.4")
        assert result == "52.500000, 13.400000"

    def test_empty_lat(self):
        assert _format_coordinates("", "13.4") == "-"

    def test_empty_lng(self):
        assert _format_coordinates("52.5", "") == "-"

    def test_both_empty(self):
        assert _format_coordinates("", "") == "-"

    def test_non_numeric(self):
        assert _format_coordinates("abc", "def") == "-"
