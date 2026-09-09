"""Unit tests for the coordinate form field and its cross-field validation."""

from werkzeug.datastructures import MultiDict

from app.forms import MantisSightingForm

SWAPPED = "Breiten- und Längengrad scheinen vertauscht zu sein."


def _validated(app, latitude, longitude):
    """Validate a form carrying only the two coordinate fields."""
    with app.test_request_context():
        form = MantisSightingForm(
            formdata=MultiDict({"latitude": latitude, "longitude": longitude})
        )
        form.validate()
        return form


class TestCoordinateField:
    """The field itself — parsing and its German messages."""

    def test_comma_decimals_accepted(self, app):
        """A German phone keypad emits commas; parseFloat would drop the rest."""
        form = _validated(app, "52,520008", "13,404954")

        assert (form.latitude.data, form.longitude.data) == (52.520008, 13.404954)
        assert form.latitude.errors == []
        assert form.longitude.errors == []

    def test_unparsable_value_gets_one_german_error(self, app):
        """No English WTForms message, and no range error about a non-number."""
        form = _validated(app, "abc", "13.4")

        assert form.latitude.errors == ["Breitengrad ist keine gültige Zahl."]
        assert form.longitude.errors == []

    def test_missing_value_reports_required(self, app):
        form = _validated(app, "", "13.4")

        assert form.latitude.errors == ["Breitengrad ist erforderlich (Karte nutzen)."]


class TestCoordinateFormValidation:
    """The validator chain across both fields."""

    def test_transposed_pair_reported_once_per_field(self, app):
        form = _validated(app, "13.404954", "52.520008")

        assert form.latitude.errors == [SWAPPED]
        assert form.longitude.errors == [SWAPPED]

    def test_out_of_range_reported_per_field(self, app):
        form = _validated(app, "69.224997", "-23.552937")

        assert form.latitude.errors == ["Breitengrad muss zwischen 24,6 und 60 liegen."]
        assert form.longitude.errors == ["Längengrad muss zwischen -20 und 44,83 liegen."]

    def test_valid_pair_has_no_errors(self, app):
        form = _validated(app, "52.520008", "13.404954")

        assert form.latitude.errors == []
        assert form.longitude.errors == []
