"""Custom validators for WTForms that use centralized validation logic."""
from wtforms.validators import ValidationError
from app.tools.coordinate_validation import validate_and_normalize_coordinate


class CoordinateValidator:
    """
    Validator for coordinate fields that uses centralized validation logic.
    
    This validator can be used with WTForms FloatField to ensure coordinates
    are valid and within the correct range.
    """
    
    def __init__(self, coord_type, message=None):
        """
        Initialize the validator.
        
        Args:
            coord_type: Either 'latitude' or 'longitude'
            message: Optional custom error message
        """
        self.coord_type = coord_type
        self.message = message
    
    def __call__(self, form, field):
        """
        Validate the coordinate field.
        
        Args:
            form: The form instance
            field: The field to validate
            
        Raises:
            ValidationError: If the coordinate is invalid
        """
        if field.data is None:
            return  # Let Required validator handle this
        
        is_valid, _, error_msg = validate_and_normalize_coordinate(field.data, self.coord_type)
        
        if not is_valid:
            message = self.message or error_msg or f"Invalid {self.coord_type}"
            raise ValidationError(message)