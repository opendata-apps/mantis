"""Custom validators for WTForms that use centralized validation logic."""

from wtforms.validators import StopValidation, ValidationError

from app.tools.coordinate_validation import (
    SWAPPED_MESSAGE,
    coordinates_look_swapped,
    validate_and_normalize_coordinate,
)


class CoordinateValidator:
    """Checks one coordinate field against the accepted range."""

    def __init__(self, coord_type):
        self.coord_type = coord_type

    def __call__(self, form, field):
        if field.data is None:
            return  # Let Required validator handle this

        is_valid, _, error_msg = validate_and_normalize_coordinate(
            field.data, self.coord_type
        )
        if not is_valid:
            raise ValidationError(error_msg)


class SwappedCoordinateValidator:
    """
    Rejects a transposed latitude/longitude pair.

    Reads both fields off the form, so it can hang on either one. Place it
    before CoordinateValidator: it stops the chain so the reporter gets the
    "swapped" hint instead of two range errors that don't explain anything.
    """

    def __init__(self, latitude_field="latitude", longitude_field="longitude"):
        self.latitude_field = latitude_field
        self.longitude_field = longitude_field

    def __call__(self, form, field):
        latitude = getattr(form, self.latitude_field, None)
        longitude = getattr(form, self.longitude_field, None)
        if latitude is None or longitude is None:
            return
        if latitude.data is None or longitude.data is None:
            return  # Let Required validator handle this

        if coordinates_look_swapped(latitude.data, longitude.data):
            raise StopValidation(SWAPPED_MESSAGE)
