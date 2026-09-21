"""Unit tests for the coordinate-vs-address rule."""

from app.tools.address_plausibility import contradicts_german_land


class TestContradictsGermanLand:
    def test_bundesland_with_point_abroad(self):
        """Kieselbronn typed, pin in the Egyptian desert."""
        assert contradicts_german_land(24.9, 24.9, "Baden-Württemberg")

    def test_bundesland_with_matching_point(self):
        assert not contradicts_german_land(48.9, 8.75, "Baden-Württemberg")

    def test_foreign_land_anywhere(self):
        """A holiday sighting names a foreign region and stays untouched."""
        assert not contradicts_german_land(45.53, 10.55, "Lombardei")
        assert not contradicts_german_land(52.52, 13.4, "Lombardei")

    def test_case_and_whitespace_ignored(self):
        assert contradicts_german_land(24.9, 24.9, "  NIEDERSACHSEN ")

    def test_country_counts_as_a_german_claim(self):
        assert contradicts_german_land(24.9, 24.9, "Deutschland")

    def test_abbreviation_is_not_matched(self):
        """Documented gap: an alias table would be guesswork."""
        assert not contradicts_german_land(24.9, 24.9, "NRW")

    def test_border_pin_stays_inside(self):
        """Guben sits where VG250 coverage frays; the box has slack for it."""
        assert not contradicts_german_land(51.949, 14.716, "Brandenburg")

    def test_missing_input_is_not_a_contradiction(self):
        assert not contradicts_german_land(None, 24.9, "Bayern")
        assert not contradicts_german_land(24.9, None, "Bayern")
        assert not contradicts_german_land(24.9, 24.9, "")
