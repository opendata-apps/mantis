"""Tests for AGS reference data integrity."""

from app.database.ags import (
    BUNDESLAENDER,
    BERLIN_BEZIRKE,
    BRANDENBURG_LANDKREISE,
    build_gesamt_template,
)


class TestBundeslaender:
    def test_has_all_16_states(self):
        assert len(BUNDESLAENDER) == 16

    def test_codes_are_two_digits(self):
        for code in BUNDESLAENDER:
            assert len(code) == 2 and code.isdigit()

    def test_codes_cover_01_to_16(self):
        expected = {f"{i:02d}" for i in range(1, 17)}
        assert set(BUNDESLAENDER.keys()) == expected

    def test_no_invisible_unicode(self):
        """Regression: hidden U+2060 WORD JOINER characters were present."""
        for name in BUNDESLAENDER.values():
            assert "\u2060" not in name, f"Hidden unicode in: {name!r}"


class TestBerlinBezirke:
    def test_has_13_entries(self):
        """12 Bezirke + 1 'allgemein' entry."""
        assert len(BERLIN_BEZIRKE) == 13

    def test_codes_start_with_11(self):
        for code in BERLIN_BEZIRKE:
            assert code.startswith("11")

    def test_codes_are_eight_digits(self):
        for code in BERLIN_BEZIRKE:
            assert len(code) == 8 and code.isdigit()


class TestBrandenburgLandkreise:
    def test_has_18_entries(self):
        """14 Landkreise + 4 kreisfreie Städte."""
        assert len(BRANDENBURG_LANDKREISE) == 18

    def test_codes_start_with_12(self):
        for code in BRANDENBURG_LANDKREISE:
            assert code.startswith("12")

    def test_codes_are_five_digits(self):
        for code in BRANDENBURG_LANDKREISE:
            assert len(code) == 5 and code.isdigit()


class TestBuildGesamtTemplate:
    def test_contains_all_states(self):
        result = build_gesamt_template()
        for code in BUNDESLAENDER:
            assert code in result
            assert result[code][0] == BUNDESLAENDER[code]

    def test_contains_all_brandenburg_landkreise(self):
        result = build_gesamt_template()
        for code in BRANDENBURG_LANDKREISE:
            assert code in result
            assert result[code][1] == BRANDENBURG_LANDKREISE[code]

    def test_state_entries_have_correct_structure(self):
        result = build_gesamt_template()
        for code in BUNDESLAENDER:
            entry = result[code]
            assert entry[0] != ""  # state name filled
            assert entry[1] == ""  # district name empty
            assert entry[2] == ""  # amt name empty
            assert entry[3] == 0   # count starts at zero
            assert entry[4] == []  # sub-rows empty

    def test_district_entries_have_correct_structure(self):
        result = build_gesamt_template()
        for code in BRANDENBURG_LANDKREISE:
            entry = result[code]
            assert entry[0] == ""  # state name empty
            assert entry[1] != ""  # district name filled
            assert entry[3] == 0
            assert entry[4] == []

    def test_returns_fresh_copy(self):
        """Each call returns a new dict so mutations don't affect other callers."""
        a = build_gesamt_template()
        b = build_gesamt_template()
        a["12"][3] = 999
        assert b["12"][3] == 0
