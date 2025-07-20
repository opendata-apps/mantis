"""Unit tests for coordinate validation module."""
from app.tools.coordinate_validation import (
    validate_and_normalize_coordinate,
    validate_coordinate_pair,
    is_coordinate_in_germany
)


class TestCoordinateValidation:
    """Test suite for coordinate validation functions."""
    
    def test_validate_latitude_valid(self):
        """Test validation of valid latitude values."""
        test_cases = [
            ('52.520008', '52.520008'),    # Normal value
            ('52.52', '52.52'),             # Short decimal
            (' 52.52 ', '52.52'),           # With spaces
            ('+52.52', '52.52'),            # With plus sign
            ('52,52', '52.52'),             # Comma as decimal separator
            (-89.9, '-89.9'),               # Float input
            (0, '0.0'),                     # Zero
            ('90', '90.0'),                 # Max value
            ('-90', '-90.0'),               # Min value
        ]
        
        for input_val, expected in test_cases:
            is_valid, normalized, error = validate_and_normalize_coordinate(input_val, 'latitude')
            assert is_valid is True, f"Expected {input_val} to be valid"
            assert normalized == expected, f"Expected {input_val} to normalize to {expected}, got {normalized}"
            assert error is None
    
    def test_validate_latitude_invalid(self):
        """Test validation of invalid latitude values."""
        test_cases = [
            ('91', 'Latitude must be between -90 and 90'),
            ('-91', 'Latitude must be between -90 and 90'),
            ('invalid', 'Invalid latitude format'),
            ('', 'Latitude is required'),
            (None, 'Latitude is required'),
            ('52.52.52', 'Invalid latitude format'),
            ('abc123', 'Invalid latitude format'),
        ]
        
        for input_val, expected_error in test_cases:
            is_valid, normalized, error = validate_and_normalize_coordinate(input_val, 'latitude')
            assert is_valid is False, f"Expected {input_val} to be invalid"
            assert normalized is None
            assert error == expected_error
    
    def test_validate_longitude_valid(self):
        """Test validation of valid longitude values."""
        test_cases = [
            ('13.404954', '13.404954'),    # Normal value
            ('13.40', '13.4'),              # Trailing zero removed
            (' -74.006 ', '-74.006'),       # Negative with spaces
            ('+139.6503', '139.6503'),      # With plus sign
            ('13,404954', '13.404954'),     # Comma as decimal separator
            (180, '180.0'),                 # Max value
            (-180, '-180.0'),               # Min value
        ]
        
        for input_val, expected in test_cases:
            is_valid, normalized, error = validate_and_normalize_coordinate(input_val, 'longitude')
            assert is_valid is True, f"Expected {input_val} to be valid"
            assert normalized == expected, f"Expected {input_val} to normalize to {expected}, got {normalized}"
            assert error is None
    
    def test_validate_longitude_invalid(self):
        """Test validation of invalid longitude values."""
        test_cases = [
            ('181', 'Longitude must be between -180 and 180'),
            ('-181', 'Longitude must be between -180 and 180'),
            ('not_a_number', 'Invalid longitude format'),
            ('', 'Longitude is required'),
            (None, 'Longitude is required'),
        ]
        
        for input_val, expected_error in test_cases:
            is_valid, normalized, error = validate_and_normalize_coordinate(input_val, 'longitude')
            assert is_valid is False, f"Expected {input_val} to be invalid"
            assert normalized is None
            assert error == expected_error
    
    def test_validate_coordinate_pair(self):
        """Test validation of coordinate pairs."""
        # Valid pair
        is_valid, lat, lon, errors = validate_coordinate_pair('52.52', '13.40')
        assert is_valid is True
        assert lat == '52.52'
        assert lon == '13.4'
        assert errors == []
        
        # Invalid latitude
        is_valid, lat, lon, errors = validate_coordinate_pair('91', '13.40')
        assert is_valid is False
        assert lat is None
        assert lon == '13.4'
        assert len(errors) == 1
        assert 'Latitude must be between -90 and 90' in errors[0]
        
        # Both invalid
        is_valid, lat, lon, errors = validate_coordinate_pair('invalid', 'also_invalid')
        assert is_valid is False
        assert lat is None
        assert lon is None
        assert len(errors) == 2
    
    def test_is_coordinate_in_germany(self):
        """Test checking if coordinates are within Germany."""
        # Within Germany
        assert is_coordinate_in_germany('52.520008', '13.404954') is True  # Berlin
        assert is_coordinate_in_germany('48.1351', '11.5820') is True      # Munich
        assert is_coordinate_in_germany('53.5511', '9.9937') is True       # Hamburg
        
        # Outside Germany
        assert is_coordinate_in_germany('40.7128', '-74.0060') is False    # New York
        assert is_coordinate_in_germany('35.6762', '139.6503') is False    # Tokyo
        assert is_coordinate_in_germany('51.5074', '-0.1278') is False     # London (close but outside)
        
        # Invalid coordinates
        assert is_coordinate_in_germany('invalid', '13.404954') is False
        assert is_coordinate_in_germany('52.520008', 'invalid') is False
        assert is_coordinate_in_germany(None, None) is False
    
    def test_normalize_edge_cases(self):
        """Test normalization of edge cases."""
        # Multiple spaces and signs
        is_valid, normalized, _ = validate_and_normalize_coordinate('  +52.520000  ', 'latitude')
        assert is_valid is True
        assert normalized == '52.52'
        
        # Scientific notation
        is_valid, normalized, _ = validate_and_normalize_coordinate('5.252e1', 'latitude')
        assert is_valid is True
        assert normalized == '52.52'
        
        # Very small values
        is_valid, normalized, _ = validate_and_normalize_coordinate('0.0001', 'latitude')
        assert is_valid is True
        assert normalized == '0.0001'
        
        # Negative zero
        is_valid, normalized, _ = validate_and_normalize_coordinate('-0.0', 'latitude')
        assert is_valid is True
        assert normalized == '-0.0'