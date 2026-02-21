"""Unit tests for the coordinate-vs-address validation logic."""

from types import SimpleNamespace

from app.tools.validate_coordinates import (
    Issue,
    names_match,
    validate_fundorte,
    format_report,
    format_csv,
)


class TestNamesMatch:
    """Test substring containment matching."""

    def test_exact_match(self):
        assert names_match("Berlin", "Berlin")

    def test_case_insensitive(self):
        assert names_match("berlin", "Berlin")
        assert names_match("BERLIN", "berlin")

    def test_substring_forward(self):
        """Stored ort contains the Gemeinde name."""
        assert names_match("Berlin-Mitte", "Berlin")

    def test_substring_reverse(self):
        """Gemeinde name contains the stored ort."""
        assert names_match("Frankfurt", "Frankfurt am Main")

    def test_no_match(self):
        assert not names_match("München", "Hamburg")

    def test_empty_strings(self):
        assert not names_match("", "Berlin")
        assert not names_match("Berlin", "")
        assert not names_match("", "")

    def test_whitespace_handling(self):
        assert names_match("  Berlin  ", "Berlin")
        assert names_match("Berlin", "  Berlin  ")

    def test_partial_no_match(self):
        """Wannsee is a Stadtteil but not in the Gemeinde name 'Berlin'."""
        assert not names_match("Wannsee", "Berlin")

    def test_compound_name(self):
        assert names_match("Bad Freienwalde", "Bad Freienwalde (Oder)")

    def test_forst_lausitz(self):
        assert names_match("Forst (Lausitz)", "Forst (Lausitz)")


def _fundort(id, lat, lon, ort, land):
    """Helper to create a minimal Fundort-like object."""
    return SimpleNamespace(
        id=id, latitude=str(lat), longitude=str(lon), ort=ort, land=land
    )


class TestValidateFundorte:
    """Test the validation logic with mock spatial lookups."""

    def _spatial_berlin(self, point):
        """Mock: everything resolves to Berlin."""
        return {"land": "Berlin", "gen": "Berlin", "kreis": "Berlin", "ags": "11000000"}

    def _spatial_none(self, point):
        """Mock: everything is outside Germany."""
        return None

    def _spatial_by_region(self, point):
        """Mock: return different results based on longitude."""
        lon, lat = point
        if lon < 10:
            return {"land": "Hamburg", "gen": "Hamburg", "kreis": "Hamburg", "ags": "02000000"}
        return {"land": "Berlin", "gen": "Berlin", "kreis": "Berlin", "ags": "11000000"}

    def test_matching_fundort_no_mismatch(self):
        fundorte = [_fundort(1, 52.52, 13.38, "Berlin", "Berlin")]
        mismatches, checked, skipped = validate_fundorte(fundorte, self._spatial_berlin)
        assert checked == 1
        assert skipped == 0
        assert len(mismatches) == 0

    def test_land_mismatch(self):
        fundorte = [_fundort(1, 52.52, 13.38, "Berlin", "Bayern")]
        mismatches, checked, skipped = validate_fundorte(fundorte, self._spatial_berlin)
        assert len(mismatches) == 1
        assert mismatches[0].issue == Issue.LAND_MISMATCH
        assert mismatches[0].stored_land == "Bayern"
        assert mismatches[0].expected_land == "Berlin"

    def test_ort_mismatch(self):
        fundorte = [_fundort(1, 52.52, 13.38, "München", "Berlin")]
        mismatches, checked, skipped = validate_fundorte(fundorte, self._spatial_berlin)
        assert len(mismatches) == 1
        assert mismatches[0].issue == Issue.ORT_MISMATCH
        assert mismatches[0].stored_ort == "München"
        assert mismatches[0].expected_ort == "Berlin"

    def test_outside_germany(self):
        fundorte = [_fundort(1, 48.85, 2.35, "Paris", "Frankreich")]
        mismatches, checked, skipped = validate_fundorte(fundorte, self._spatial_none)
        assert len(mismatches) == 1
        assert mismatches[0].issue == Issue.OUTSIDE_DE

    def test_invalid_coordinates_skipped(self):
        fundorte = [_fundort(1, "abc", "def", "Berlin", "Berlin")]
        mismatches, checked, skipped = validate_fundorte(fundorte, self._spatial_berlin)
        assert checked == 0
        assert skipped == 1
        assert len(mismatches) == 0

    def test_empty_latitude_skipped(self):
        fundorte = [_fundort(1, "", "13.38", "Berlin", "Berlin")]
        mismatches, checked, skipped = validate_fundorte(fundorte, self._spatial_berlin)
        assert skipped == 1

    def test_land_mismatch_skips_ort_check(self):
        """When land is wrong, we skip the ort check (redundant)."""
        fundorte = [_fundort(1, 52.52, 8.0, "Hamburg", "Hamburg")]
        mismatches, checked, skipped = validate_fundorte(
            fundorte, self._spatial_by_region
        )
        assert len(mismatches) == 0  # lon < 10 → Hamburg, matches

        fundorte2 = [_fundort(2, 52.52, 8.0, "München", "Bayern")]
        mismatches2, _, _ = validate_fundorte(fundorte2, self._spatial_by_region)
        assert len(mismatches2) == 1
        assert mismatches2[0].issue == Issue.LAND_MISMATCH
        # Only LAND_MISMATCH, not also ORT_MISMATCH

    def test_substring_ort_match_passes(self):
        """Berlin-Mitte should match Gemeinde 'Berlin'."""
        fundorte = [_fundort(1, 52.52, 13.38, "Berlin-Mitte", "Berlin")]
        mismatches, checked, skipped = validate_fundorte(fundorte, self._spatial_berlin)
        assert len(mismatches) == 0

    def test_multiple_fundorte(self):
        fundorte = [
            _fundort(1, 52.52, 13.38, "Berlin", "Berlin"),   # OK
            _fundort(2, 52.52, 13.38, "München", "Bayern"),   # LAND mismatch
            _fundort(3, 48.85, 2.35, "Paris", "Frankreich"),  # outside DE
        ]
        mismatches, checked, skipped = validate_fundorte(
            fundorte,
            lambda pt: self._spatial_berlin(pt) if pt[0] > 10 else None,
        )
        assert checked == 3
        assert len(mismatches) == 2


class TestFormatReport:
    """Test report formatting."""

    def test_no_mismatches(self):
        report = format_report([], checked=100, skipped=2)
        assert "No mismatches found" in report
        assert "Checked: 100" in report

    def test_with_mismatches(self):
        from app.tools.validate_coordinates import Mismatch

        m = Mismatch(42, Issue.LAND_MISMATCH, "Bayern", "Berlin", "München", "Berlin")
        report = format_report([m], checked=100, skipped=0)
        assert "42" in report
        assert "LAND_MISMATCH" in report
        assert "Bayern" in report


class TestFormatCsv:
    """Test CSV formatting."""

    def test_csv_header(self):
        csv = format_csv([])
        assert csv.startswith("id,issue,stored_land,expected_land")

    def test_csv_row(self):
        from app.tools.validate_coordinates import Mismatch

        m = Mismatch(42, Issue.LAND_MISMATCH, "Bayern", "Berlin", "München", "Berlin")
        csv = format_csv([m])
        lines = csv.split("\n")
        assert len(lines) == 2
        assert "42" in lines[1]
        assert "LAND_MISMATCH" in lines[1]
