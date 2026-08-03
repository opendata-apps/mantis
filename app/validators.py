"""Custom form fields and validators built on the coordinate rules."""

from wtforms import FloatField
from wtforms.validators import NumberRange, StopValidation

from app.tools.coordinate_validation import (
    RANGES,
    SWAPPED_MESSAGE,
    coordinates_look_swapped,
    invalid_number_message,
    parse_coordinate,
    range_message,
)


class CoordinateField(FloatField):
    """
    Float field for one coordinate axis.

    Owns everything axis-specific: comma decimals (a German phone shows one on
    the ``inputmode="decimal"`` keypad), German messages, and the accepted
    range — so a form only has to say which axis it is.
    """

    def __init__(self, label=None, validators=None, coord_type="latitude", **kwargs):
        self.coord_type = coord_type
        low, high = RANGES[coord_type]
        super().__init__(
            label,
            [
                *(validators or []),
                NumberRange(min=low, max=high, message=range_message(coord_type)),
            ],
            **kwargs,
        )

    def process_formdata(self, valuelist):
        if not valuelist or not str(valuelist[0]).strip():
            return  # emptiness is the Required validator's business

        number = parse_coordinate(valuelist[0])
        if number is None:
            self.data = None
            raise ValueError(invalid_number_message(self.coord_type))

        self.data = number

    def pre_validate(self, form):
        # Coercion already failed, so range and swap complaints about a value
        # that is not a number would only bury the message that matters.
        if self.process_errors:
            raise StopValidation()


class SwappedCoordinateValidator:
    """
    Rejects a transposed latitude/longitude pair.

    Reads both coordinate fields off the form, so it can hang on either one.
    """

    def __call__(self, form, field):
        latitude, longitude = form.latitude.data, form.longitude.data
        if latitude is None or longitude is None:
            return  # the other field reports its own problem

        if coordinates_look_swapped(latitude, longitude):
            raise StopValidation(SWAPPED_MESSAGE)
