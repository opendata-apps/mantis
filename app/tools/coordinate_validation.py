"""Centralized coordinate validation and normalization utilities."""


def validate_and_normalize_coordinate(value, coord_type):
    """
    Validate and normalize a coordinate value.
    
    Args:
        value: The coordinate value to validate (can be string, float, or None)
        coord_type: Either 'latitude' or 'longitude'
    
    Returns:
        tuple: (is_valid, normalized_value, error_message)
            - is_valid: Boolean indicating if the coordinate is valid
            - normalized_value: The normalized coordinate as a string, or None if invalid
            - error_message: Error message if invalid, None if valid
    
    Examples:
        >>> validate_and_normalize_coordinate('52.520000', 'latitude')
        (True, '52.52', None)
        
        >>> validate_and_normalize_coordinate('91.0', 'latitude')
        (False, None, 'Latitude must be between -90 and 90')
        
        >>> validate_and_normalize_coordinate(' 13.40 ', 'longitude')
        (True, '13.4', None)
    """
    if value is None or value == '':
        return False, None, f"{coord_type.capitalize()} is required"
    
    try:
        # Convert to string and clean up
        coord_str = str(value).strip()
        
        # Handle potential comma as decimal separator (legacy data)
        coord_str = coord_str.replace(',', '.')
        
        # Remove plus sign if present
        coord_str = coord_str.lstrip('+')
        
        # Convert to float for validation
        coord_value = float(coord_str)
        
        # Validate range based on type
        if coord_type == 'latitude':
            if not (-90 <= coord_value <= 90):
                return False, None, "Latitude must be between -90 and 90"
        elif coord_type == 'longitude':
            if not (-180 <= coord_value <= 180):
                return False, None, "Longitude must be between -180 and 180"
        else:
            return False, None, f"Invalid coordinate type: {coord_type}"
        
        # Return normalized value (removes trailing zeros)
        normalized = str(coord_value)
        return True, normalized, None
        
    except (ValueError, TypeError):
        return False, None, f"Invalid {coord_type} format"


def validate_coordinate_pair(latitude, longitude):
    """
    Validate a pair of coordinates together.
    
    Args:
        latitude: The latitude value
        longitude: The longitude value
    
    Returns:
        tuple: (is_valid, normalized_lat, normalized_lon, errors)
            - is_valid: Boolean indicating if both coordinates are valid
            - normalized_lat: Normalized latitude or None
            - normalized_lon: Normalized longitude or None  
            - errors: List of error messages
    """
    errors = []
    
    lat_valid, normalized_lat, lat_error = validate_and_normalize_coordinate(latitude, 'latitude')
    if not lat_valid:
        errors.append(lat_error)
    
    lon_valid, normalized_lon, lon_error = validate_and_normalize_coordinate(longitude, 'longitude')
    if not lon_valid:
        errors.append(lon_error)
    
    is_valid = len(errors) == 0
    return is_valid, normalized_lat, normalized_lon, errors


def is_coordinate_in_germany(latitude, longitude):
    """
    Check if coordinates are within Germany's approximate bounds.
    
    Germany approximate bounds:
    - Latitude: 47.3 to 55.1
    - Longitude: 5.9 to 15.0
    
    Args:
        latitude: float or string latitude
        longitude: float or string longitude
        
    Returns:
        bool: True if coordinates are within Germany's bounds
    """
    try:
        lat = float(latitude)
        lon = float(longitude)
        return 47.3 <= lat <= 55.1 and 5.9 <= lon <= 15.0
    except (ValueError, TypeError):
        return False