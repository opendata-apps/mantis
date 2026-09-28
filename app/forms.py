from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired, FileSize
from wtforms import (
    FloatField,
    StringField,
    TextAreaField,
    DateField,
    SelectField,
    BooleanField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    NumberRange,
    Optional,
    Length,
    StopValidation,
    ValidationError,
    InputRequired,
)
from datetime import date
from dateutil.relativedelta import relativedelta

from app.database.feedback_type import FeedbackSource
from app.tools.address_plausibility import contradicts_german_land
from app.tools.coordinate_validation import (
    INVALID_MESSAGES,
    LAT_RANGE,
    LON_RANGE,
    RANGE_MESSAGES,
    SWAPPED_MESSAGE,
    coordinates_look_swapped,
    in_range,
    parse_coordinate,
)
from app.tools.image_upload import (
    MAX_UPLOAD_BYTES,
    allowed_extensions,
    display_formats,
    max_upload_mb,
)
from app.tools.postal_code import is_valid_plz


# Define constants for choices
GENDER_CHOICES = [
    ("", "-- Bitte wählen --"),
    ("Unbekannt", "Unbekannt"),
    ("Männlich", "Männlich"),
    ("Weiblich", "Weiblich"),
    ("Nymphe", "Nymphe"),
    ("Oothek", "Oothek (Eipaket)"),
]

LOCATION_DESCRIPTION_CHOICES = [
    ("", "-- Bitte wählen --"),
    ("1", "Innenräume"),
    ("2", "Garten"),
    ("3", "Balkon/Terrasse"),
    ("4", "Fenster/Wand"),
    ("5", "Industriegebiet"),
    ("6", "Wald"),
    ("7", "Wiese/Weide"),
    ("8", "Heide"),
    ("9", "Straßenrand/Weg"),
    ("10", "Gewerbegebiet"),
    ("11", "In/an einem Fahrzeug"),
    ("99", "Andere Orte"),
]

FEEDBACK_SOURCE_CHOICES = FeedbackSource.choices()


# Custom validators
def minimum_sighting_date() -> date:
    return date.today() - relativedelta(years=5)


def validate_past_date(form, field):
    if field.data:
        today = date.today()
        if field.data > today:
            raise ValidationError("Datum darf nicht in der Zukunft liegen.")
        if field.data < minimum_sighting_date():
            raise ValidationError("Datum liegt zu weit zurück (max. 5 Jahre).")


def validate_zip_code(form, field):
    if field.data and not is_valid_plz(field.data):
        raise ValidationError("Postleitzahl muss genau 5 Ziffern haben.")


class CoordinateField(FloatField):
    """FloatField that parses with parse_coordinate: accepts the comma decimal
    and fails with a German message instead of "Not a valid float value."."""

    def __init__(self, label=None, validators=None, coord_type="latitude", **kwargs):
        super().__init__(label, validators, **kwargs)
        self.coord_type = coord_type

    def process_formdata(self, valuelist):
        if not valuelist:
            return

        self.data = parse_coordinate(valuelist[0])
        if self.data is None:
            raise ValueError(INVALID_MESSAGES[self.coord_type])


def validate_not_swapped(form, field):
    """Reject a transposed latitude/longitude pair.

    Hangs on both coordinate fields and reads the other one off the form. Place
    it before NumberRange: it stops the chain so the reporter gets the "swapped"
    hint instead of two range errors that don't explain anything.
    """
    if field.data is None:
        # Parsing failed and recorded its error; NumberRange would add another.
        raise StopValidation()

    other = form.longitude if field is form.latitude else form.latitude
    if other.data is None:
        return  # nothing to compare against yet

    if coordinates_look_swapped(form.latitude.data, form.longitude.data):
        raise StopValidation(SWAPPED_MESSAGE)


def validate_land_matches_point(form, field):
    """Reject a pin far outside Germany while the form claims a Bundesland.

    Belongs on latitude only; both axes report into one error slot.
    """
    latitude, longitude = form.latitude.data, form.longitude.data
    if latitude is None or longitude is None or not in_range(latitude, longitude):
        return  # the parse and range validators already reported these

    if not contradicts_german_land(latitude, longitude, form.fund_state.data):
        return

    raise ValidationError(
        "Der markierte Punkt liegt nicht in Deutschland, als Bundesland ist "
        f"aber „{form.fund_state.data}“ angegeben. Bitte den Fundort auf der "
        "Karte markieren oder das Bundesland korrigieren."
    )


def _strip(value):
    """Trim string input; dates, files and bools pass through untouched."""
    return value.strip() if isinstance(value, str) else value


class StrippedForm(FlaskForm):
    """Base form that adds _strip to every field's filters (WTForms strips
    nothing by default)."""

    class Meta:
        def bind_field(self, form, unbound_field, options):
            filters = list(unbound_field.kwargs.get("filters", []))
            if _strip not in filters:
                filters.append(_strip)
            return unbound_field.bind(form=form, filters=filters, **options)


# Define WTForms form class for the sighting report
class MantisSightingForm(StrippedForm):
    # Observer Information
    report_first_name = StringField(
        "Vorname *",
        validators=[
            DataRequired(message="Vorname ist erforderlich."),
            Length(
                min=1,
                max=50,
                message="Vorname muss zwischen 1 und 50 Zeichen lang sein.",
            ),
        ],
        render_kw={"placeholder": "Ihr Vorname", "autocomplete": "given-name"},
    )
    report_last_name = StringField(
        "Nachname *",
        validators=[
            DataRequired(message="Nachname ist erforderlich."),
            Length(
                min=1,
                max=50,
                message="Nachname muss zwischen 1 und 50 Zeichen lang sein.",
            ),
        ],
        render_kw={"placeholder": "Ihr Nachname", "autocomplete": "family-name"},
    )
    email = StringField(
        "E-Mail",
        validators=[
            Optional(),
            Email(
                message="Bitte geben Sie eine gültige E-Mail-Adresse ein.",
                check_deliverability=False,
                # An umlaut in the local part needs SMTPUTF8 along the whole
                # path; Flask-Mail submits through smtplib.sendmail, which has
                # none, so the send raises long after the report was accepted.
                # A non-ASCII domain is fine and handled at submission.
                allow_smtputf8=False,
            ),
            Length(
                max=120,
                message="Die E-Mail-Adresse darf maximal 120 Zeichen lang sein.",
            ),
        ],
        render_kw={"placeholder": "ihre.email@beispiel.de", "autocomplete": "email"},
    )
    identical_finder_reporter = BooleanField(
        "Ich bin der Finder dieser Gottesanbeterin"
    )
    finder_first_name = StringField(
        "Vorname des Finders",
        validators=[
            Optional(),
            Length(
                min=1,
                max=50,
                message="Vorname muss zwischen 1 und 50 Zeichen lang sein.",
            ),
        ],
        render_kw={"placeholder": "Vorname (falls abweichend)", "autocomplete": "off"},
    )
    finder_last_name = StringField(
        "Nachname des Finders",
        validators=[
            Optional(),
            Length(
                min=1,
                max=50,
                message="Nachname muss zwischen 1 und 50 Zeichen lang sein.",
            ),
        ],
        render_kw={"placeholder": "Nachname (falls abweichend)", "autocomplete": "off"},
    )

    # Feedback Information - How did you hear about us?
    feedback_source = SelectField(
        "Wie sind Sie auf unser Projekt aufmerksam geworden?",
        choices=FEEDBACK_SOURCE_CHOICES,
        validators=[Optional()],
        render_kw={"title": "Feedback-Quelle auswählen"},
    )
    feedback_detail = StringField(
        "Details (optional)",
        validators=[
            Optional(),
            Length(max=255, message="Details dürfen maximal 255 Zeichen lang sein."),
        ],
        render_kw={
            "placeholder": "z.B. Name der Veranstaltung, Website, etc.",
            "autocomplete": "off",
        },
    )

    # Sighting Details
    sighting_date = DateField(
        "Datum der Sichtung *",
        format="%Y-%m-%d",
        validators=[
            DataRequired(message="Sichtungsdatum ist erforderlich."),
            validate_past_date,
        ],
        render_kw={"placeholder": "JJJJ-MM-TT", "autocomplete": "off"},
    )

    # Location Information
    latitude = CoordinateField(
        "Breitengrad *",
        coord_type="latitude",
        validators=[
            InputRequired(message="Breitengrad ist erforderlich (Karte nutzen)."),
            validate_not_swapped,
            NumberRange(
                min=LAT_RANGE[0],
                max=LAT_RANGE[1],
                message=RANGE_MESSAGES["latitude"],
            ),
            validate_land_matches_point,
        ],
        render_kw={"readonly": True, "aria-label": "Breitengrad (von Karte gesetzt)"},
    )
    longitude = CoordinateField(
        "Längengrad *",
        coord_type="longitude",
        validators=[
            InputRequired(message="Längengrad ist erforderlich (Karte nutzen)."),
            validate_not_swapped,
            NumberRange(
                min=LON_RANGE[0],
                max=LON_RANGE[1],
                message=RANGE_MESSAGES["longitude"],
            ),
        ],
        render_kw={"readonly": True, "aria-label": "Längengrad (von Karte gesetzt)"},
    )
    # Address of the sighting, not of the reporter.
    fund_zip_code = StringField(
        "Postleitzahl",
        validators=[Optional(), validate_zip_code],
        render_kw={"placeholder": "z.B. 10115", "autocomplete": "off"},
    )
    fund_city = StringField(
        "Stadt/Ort *",
        validators=[
            DataRequired(message="Stadt/Ort ist erforderlich."),
            Length(max=100, message="Der Ort darf maximal 100 Zeichen lang sein."),
        ],
        render_kw={
            "placeholder": "Name der Stadt oder des Ortes",
            "autocomplete": "off",
        },
    )
    fund_street = StringField(
        "Straße",
        validators=[
            Optional(),
            Length(max=100, message="Die Straße darf maximal 100 Zeichen lang sein."),
        ],
        render_kw={
            "placeholder": "Straßenname (optional)",
            "autocomplete": "off",
        },
    )
    fund_state = StringField(
        "Bundesland *",
        validators=[
            DataRequired(message="Bundesland ist erforderlich."),
            Length(max=50, message="Das Bundesland darf maximal 50 Zeichen lang sein."),
        ],
        render_kw={"placeholder": "Bundesland", "autocomplete": "off"},
    )
    fund_district = StringField(
        "Landkreis",
        validators=[
            Optional(),
            Length(
                max=100, message="Der Landkreis darf maximal 100 Zeichen lang sein."
            ),
        ],
        render_kw={
            "placeholder": "Landkreis oder Bezirk (optional)",
            "autocomplete": "off",
        },
    )

    # Mantis Details
    gender = SelectField(
        "Entwicklungsstadium/Geschlecht *",
        choices=GENDER_CHOICES,
        validators=[DataRequired(message="Bitte wählen Sie eine Option aus.")],
        render_kw={"title": "Entwicklungsstadium auswählen"},
    )
    location_description = SelectField(
        "Fundortbeschreibung *",
        choices=LOCATION_DESCRIPTION_CHOICES,
        validators=[DataRequired(message="Bitte wählen Sie einen Ortstyp aus.")],
        render_kw={"title": "Fundortbeschreibung auswählen"},
    )
    description = TextAreaField(
        "Details zum Fundort",
        validators=[
            Optional(),
            Length(
                max=500, message="Die Details dürfen maximal 500 Zeichen lang sein."
            ),
        ],
        render_kw={"placeholder": "Weitere Details (max. 500 Zeichen)", "rows": 3},
    )

    photo = FileField(
        f"Foto (max. {max_upload_mb()}MB) *",
        validators=[
            FileRequired(message="Ein Foto ist erforderlich."),
            FileAllowed(
                allowed_extensions(),
                f"Nur Bilddateien ({', '.join(display_formats())}) sind erlaubt.",
            ),
            FileSize(
                max_size=MAX_UPLOAD_BYTES,
                message=f"Das Bild darf maximal {max_upload_mb()}MB groß sein.",
            ),
        ],
    )

    # Honeypot field for spam prevention. Deliberately unvalidated — the route
    # rejects a filled trap before validation runs, and a length error here
    # would surface the field name in the errors returned to the client.
    honeypot = StringField(validators=[Optional()])

    def validate_finder_names_dependency(self):
        if not self.identical_finder_reporter.data:
            first_name_filled = bool(self.finder_first_name.data)
            last_name_filled = bool(self.finder_last_name.data)

            if first_name_filled and not last_name_filled:
                errors = self.finder_last_name.errors
                assert isinstance(errors, list)
                errors.append(
                    "Nachname des Finders ist erforderlich, wenn Vorname angegeben wurde."
                )
                return False
            if last_name_filled and not first_name_filled:
                errors = self.finder_first_name.errors
                assert isinstance(errors, list)
                errors.append(
                    "Vorname des Finders ist erforderlich, wenn Nachname angegeben wurde."
                )
                return False
        return True
