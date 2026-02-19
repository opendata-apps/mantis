"""Unit tests for pure helper functions in app/routes/report.py.

These tests exercise the helper functions directly — no Flask client or DB needed.
They catch regressions like the Männchen/Männlich mismatch that existed before.
"""

import pytest
from app.routes.report import (
    _set_gender_fields,
    _parse_user_name,
    _format_date,
    _format_coordinates,
    _get_finder_name,
    _get_gender_display,
    _get_location_description_display,
    _get_feedback_source_display,
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
# _parse_user_name
# ---------------------------------------------------------------------------
class TestParseUserName:
    """Splits DB format 'Lastname F.' → (last, first)."""

    def test_standard_format(self):
        last, first = _parse_user_name("Müller M.")
        assert last == "Müller"
        assert first == "M"

    def test_initial_format(self):
        last, first = _parse_user_name("Schmidt K.")
        assert last == "Schmidt"
        assert first == "K"

    def test_single_word(self):
        last, first = _parse_user_name("Weber")
        assert last == "Weber"
        assert first == "W"  # falls back to first char of last name

    def test_longer_first_name_part(self):
        """If the second part isn't an initial (e.g. full first name), keep it."""
        last, first = _parse_user_name("Müller Max")
        assert last == "Müller"
        assert first == "Max"

    def test_empty_string(self):
        last, first = _parse_user_name("")
        assert last == ""
        assert first == "X"  # fallback for empty


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


# ---------------------------------------------------------------------------
# _get_finder_name
# ---------------------------------------------------------------------------
class TestGetFinderName:

    def test_both_names(self):
        form = {"finder_first_name": "Max", "finder_last_name": "Müller"}
        assert _get_finder_name(form) == "Max Müller"

    def test_first_only(self):
        form = {"finder_first_name": "Max", "finder_last_name": ""}
        assert _get_finder_name(form) == "Max"

    def test_last_only(self):
        form = {"finder_first_name": "", "finder_last_name": "Müller"}
        assert _get_finder_name(form) == "Müller"

    def test_both_empty(self):
        form = {"finder_first_name": "", "finder_last_name": ""}
        assert _get_finder_name(form) == "-"

    def test_missing_keys(self):
        assert _get_finder_name({}) == "-"


# ---------------------------------------------------------------------------
# _get_gender_display  (needs app context for import)
# ---------------------------------------------------------------------------
class TestGetGenderDisplay:

    def test_known_values(self, app):
        with app.app_context():
            assert _get_gender_display("Männlich") == "Männlich"
            assert _get_gender_display("Weiblich") == "Weiblich"
            assert _get_gender_display("Nymphe") == "Nymphe"
            assert _get_gender_display("Oothek") == "Oothek (Eipaket)"
            assert _get_gender_display("Unbekannt") == "Unbekannt"

    def test_empty(self, app):
        with app.app_context():
            # Empty string matches the first choice ("", "-- Bitte wählen --")
            assert _get_gender_display("") == "-- Bitte wählen --"

    def test_unknown_value(self, app):
        with app.app_context():
            assert _get_gender_display("INVALID") == "-"


# ---------------------------------------------------------------------------
# _get_location_description_display
# ---------------------------------------------------------------------------
class TestGetLocationDescriptionDisplay:

    def test_known_ids(self, app):
        with app.app_context():
            assert _get_location_description_display("1") == "Innenräume"
            assert _get_location_description_display("2") == "Garten"
            assert _get_location_description_display("99") == "Andere Orte"

    def test_empty(self, app):
        with app.app_context():
            assert _get_location_description_display("") == "-- Bitte wählen --"

    def test_unknown_id(self, app):
        with app.app_context():
            assert _get_location_description_display("999") == "-"


# ---------------------------------------------------------------------------
# _get_feedback_source_display
# ---------------------------------------------------------------------------
class TestGetFeedbackSourceDisplay:

    def test_known_values(self):
        assert _get_feedback_source_display("EVENT") == "Auf einer Veranstaltung"
        assert _get_feedback_source_display("PRESS") == "Presse"
        assert _get_feedback_source_display("SOCIAL") == "Social Media"

    def test_empty(self):
        assert _get_feedback_source_display("") == "Nicht angegeben"

    def test_unknown(self):
        # FeedbackSource.get_display_name returns the value itself for unknowns
        assert _get_feedback_source_display("UNKNOWN") == "UNKNOWN"
