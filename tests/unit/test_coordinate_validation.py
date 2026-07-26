"""Unit tests for coordinate validation module."""

from app.tools.coordinate_validation import (
    coordinates_look_swapped,
    validate_and_normalize_coordinate,
    validate_coordinate_pair,
)

LAT_RANGE_ERROR = "Breitengrad muss zwischen 24,6 und 60 liegen."
LON_RANGE_ERROR = "Längengrad muss zwischen -20 und 44,83 liegen."


class TestCoordinateValidation:
    """Test suite for coordinate validation functions."""

    def test_validate_latitude_valid(self):
        """Test validation of valid latitude values."""
        test_cases = [
            ("52.520008", "52.520008"),  # Normal value
            ("52.52", "52.52"),  # Short decimal
            (" 52.52 ", "52.52"),  # With spaces
            ("+52.52", "52.52"),  # With plus sign
            ("52,52", "52.52"),  # Comma as decimal separator
            (24.6, "24.6"),  # Min value
            (60, "60.0"),  # Max value
            ("5.252e1", "52.52"),  # Scientific notation
        ]

        for input_val, expected in test_cases:
            is_valid, normalized, error = validate_and_normalize_coordinate(
                input_val, "latitude"
            )
            assert is_valid is True, f"Expected {input_val} to be valid"
            assert normalized == expected, (
                f"Expected {input_val} to normalize to {expected}, got {normalized}"
            )
            assert error is None

    def test_validate_latitude_invalid(self):
        """Test validation of invalid latitude values."""
        test_cases = [
            ("69.224997", LAT_RANGE_ERROR),  # North of the accepted range
            ("13.4", LAT_RANGE_ERROR),  # South of the accepted range
            ("91", LAT_RANGE_ERROR),
            ("-91", LAT_RANGE_ERROR),
            ("invalid", "Breitengrad ist keine gültige Zahl."),
            ("++13", "Breitengrad ist keine gültige Zahl."),
            ("+-13", "Breitengrad ist keine gültige Zahl."),
            ("52.52.52", "Breitengrad ist keine gültige Zahl."),
            ("nan", "Breitengrad ist keine gültige Zahl."),
            ("inf", "Breitengrad ist keine gültige Zahl."),
            ("", "Breitengrad ist erforderlich."),
            ("   ", "Breitengrad ist erforderlich."),
            (None, "Breitengrad ist erforderlich."),
        ]

        for input_val, expected_error in test_cases:
            is_valid, normalized, error = validate_and_normalize_coordinate(
                input_val, "latitude"
            )
            assert is_valid is False, f"Expected {input_val} to be invalid"
            assert normalized is None
            assert error == expected_error

    def test_validate_longitude_valid(self):
        """Test validation of valid longitude values."""
        test_cases = [
            ("13.404954", "13.404954"),  # Normal value
            ("13.40", "13.4"),  # Trailing zero removed
            (" -8.61 ", "-8.61"),  # Negative with spaces (Lisbon)
            ("+13.4", "13.4"),  # With plus sign
            ("13,404954", "13.404954"),  # Comma as decimal separator
            (-20, "-20.0"),  # Min value
            (44.83, "44.83"),  # Max value
        ]

        for input_val, expected in test_cases:
            is_valid, normalized, error = validate_and_normalize_coordinate(
                input_val, "longitude"
            )
            assert is_valid is True, f"Expected {input_val} to be valid"
            assert normalized == expected, (
                f"Expected {input_val} to normalize to {expected}, got {normalized}"
            )
            assert error is None

    def test_validate_longitude_invalid(self):
        """Test validation of invalid longitude values."""
        test_cases = [
            ("-23.552937", LON_RANGE_ERROR),  # West of the accepted range
            ("74.006", LON_RANGE_ERROR),  # East of the accepted range
            ("181", LON_RANGE_ERROR),
            ("-181", LON_RANGE_ERROR),
            ("not_a_number", "Längengrad ist keine gültige Zahl."),
            ("++13", "Längengrad ist keine gültige Zahl."),
            ("", "Längengrad ist erforderlich."),
            (None, "Längengrad ist erforderlich."),
        ]

        for input_val, expected_error in test_cases:
            is_valid, normalized, error = validate_and_normalize_coordinate(
                input_val, "longitude"
            )
            assert is_valid is False, f"Expected {input_val} to be invalid"
            assert normalized is None
            assert error == expected_error

    def test_validate_coordinate_pair(self):
        """Test validation of coordinate pairs."""
        # Valid pair
        is_valid, lat, lon, errors = validate_coordinate_pair("52.52", "13.40")
        assert is_valid is True
        assert lat == "52.52"
        assert lon == "13.4"
        assert errors == []

        # Out-of-range latitude (the Greenland Sea pin)
        is_valid, lat, lon, errors = validate_coordinate_pair("69.224997", "13.0")
        assert is_valid is False
        assert lat is None
        assert lon == "13.0"
        assert errors == [LAT_RANGE_ERROR]

        # Both invalid
        is_valid, lat, lon, errors = validate_coordinate_pair("invalid", "also_invalid")
        assert is_valid is False
        assert lat is None
        assert lon is None
        assert len(errors) == 2

    def test_transposed_pair_reported_as_swap(self):
        """A transposed pair gets the swap hint, not two range errors."""
        is_valid, lat, lon, errors = validate_coordinate_pair("13.40", "52.52")
        assert is_valid is False
        assert errors == ["Breiten- und Längengrad scheinen vertauscht zu sein."]


class TestSwappedCoordinates:
    """Test suite for transposed latitude/longitude detection."""

    def test_swapped_pairs_detected(self):
        """Transposed European coordinates are flagged."""
        test_cases = [
            (13.4, 52.52, "Berlin"),
            (11.58, 48.14, "München"),
            ("2.35", "48.86", "Paris"),
            (-0.13, 51.51, "London"),
            (18.07, 59.33, "Stockholm"),
        ]

        for lat, lon, label in test_cases:
            assert coordinates_look_swapped(lat, lon) is True, (
                f"Expected transposed {label} to be detected"
            )

    def test_correct_pairs_not_flagged(self):
        """Correctly ordered coordinates are never flagged."""
        test_cases = [
            (52.52, 13.4, "Berlin"),
            (48.14, 11.58, "München"),
            (35.9, 14.5, "Malta — southern edge"),
            (59.91, 10.75, "Oslo — near the northern edge"),
            (64.13, -21.9, "Reykjavík — out of range, but no valid swap"),
            (38.0, 38.0, "ambiguous: both values in the lat/lon overlap"),
            (39.93, 32.86, "Ankara — swap also plausible, so not flagged"),
        ]

        for lat, lon, label in test_cases:
            assert coordinates_look_swapped(lat, lon) is False, (
                f"Expected {label} not to be flagged"
            )

    def test_outside_range_both_ways_not_flagged(self):
        """Points out of range in either order are left to the range check."""
        # Tokyo — swapping does not bring it into range either
        assert coordinates_look_swapped(35.68, 139.69) is False
        assert coordinates_look_swapped(139.69, 35.68) is False

    def test_invalid_input_not_flagged(self):
        """Unparseable values are left to the per-field format check."""
        assert coordinates_look_swapped("abc", "13.4") is False
        assert coordinates_look_swapped(None, None) is False
