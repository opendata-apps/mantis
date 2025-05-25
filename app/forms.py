from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired, FileSize
from wtforms import (
    StringField,
    FloatField,
    TextAreaField,
    DateField,
    SubmitField,
    SelectField,
    BooleanField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    Optional,
    Length,
    NumberRange,
    ValidationError,
    InputRequired,
)
from datetime import date, timedelta
import re

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

# Custom validators
def validate_past_date(form, field):
    if field.data:
        today = date.today()
        if field.data > today:
            raise ValidationError("Datum darf nicht in der Zukunft liegen.")
        five_years_ago = today - timedelta(days=5*365)
        if field.data < five_years_ago:
             raise ValidationError("Datum liegt zu weit zurück (max. 5 Jahre).")


def validate_zip_code(form, field):
    if field.data and not re.match(r"^\d{5}$", field.data):
        raise ValidationError("Postleitzahl muss genau 5 Ziffern haben.")

# Define WTForms form class for the sighting report
class MantisSightingForm(FlaskForm):
    # Observer Information
    report_first_name = StringField(
        "Vorname *",
        validators=[DataRequired(message="Vorname ist erforderlich."), Length(min=1, max=50, message="Vorname muss zwischen 1 und 50 Zeichen lang sein.")],
        render_kw={"placeholder": "Ihr Vorname", "autocomplete": "given-name"},
    )
    report_last_name = StringField(
        "Nachname *",
        validators=[DataRequired(message="Nachname ist erforderlich."), Length(min=1, max=50, message="Nachname muss zwischen 1 und 50 Zeichen lang sein.")],
        render_kw={"placeholder": "Ihr Nachname", "autocomplete": "family-name"},
    )
    email = StringField(
        "E-Mail",
        validators=[
            Optional(),
            Email(
                message="Bitte geben Sie eine gültige E-Mail-Adresse ein.",
                check_deliverability=False,
            ),
            Length(max=120),
        ],
        render_kw={"placeholder": "ihre.email@beispiel.de", "autocomplete": "email"},
    )
    identical_finder_reporter = BooleanField(
        "Ich bin der Finder dieser Gottesanbeterin"
    )
    finder_first_name = StringField(
        "Vorname des Finders",
        validators=[Optional(), Length(min=1, max=50, message="Vorname muss zwischen 1 und 50 Zeichen lang sein.")],
        render_kw={"placeholder": "Vorname (falls abweichend)", "autocomplete": "off"},
    )
    finder_last_name = StringField(
        "Nachname des Finders",
        validators=[Optional(), Length(min=1, max=50, message="Nachname muss zwischen 1 und 50 Zeichen lang sein.")],
        render_kw={"placeholder": "Nachname (falls abweichend)", "autocomplete": "off"},
    )

    # Sighting Details
    sighting_date = DateField(
        "Datum der Sichtung *",
        format="%Y-%m-%d",
        validators=[
            DataRequired(message="Sichtungsdatum ist erforderlich."),
            validate_past_date,
        ],
        render_kw={"placeholder": "JJJJ-MM-TT", "autocomplete": "off"}
    )

    # Location Information
    latitude = FloatField(
        "Breitengrad *",
        validators=[
            InputRequired(message="Breitengrad ist erforderlich (Karte nutzen)."),
            NumberRange(min=-90.0, max=90.0, message="Breitengrad muss zwischen -90 und 90 liegen.")
        ],
        render_kw={"readonly": True, "aria-label": "Breitengrad (von Karte gesetzt)"}
    )
    longitude = FloatField(
        "Längengrad *",
        validators=[
            InputRequired(message="Längengrad ist erforderlich (Karte nutzen)."),
            NumberRange(min=-180.0, max=180.0, message="Längengrad muss zwischen -180 und 180 liegen.")
        ],
         render_kw={"readonly": True, "aria-label": "Längengrad (von Karte gesetzt)"}
    )
    fund_zip_code = StringField("Postleitzahl", validators=[Optional(), Length(min=5, max=5, message="PLZ muss 5 Ziffern haben."), validate_zip_code], render_kw={"placeholder": "z.B. 10115", "autocomplete": "postal-code"})
    fund_city = StringField("Stadt/Ort *", validators=[DataRequired(message="Stadt/Ort ist erforderlich."), Length(max=100)], render_kw={"placeholder": "Name der Stadt oder des Ortes", "autocomplete": "address-level2"})
    fund_street = StringField("Straße", validators=[Optional(), Length(max=100)], render_kw={"placeholder": "Straßenname (optional)", "autocomplete": "address-line1"})
    fund_state = StringField("Bundesland *", validators=[DataRequired(message="Bundesland ist erforderlich."), Length(max=50)], render_kw={"placeholder": "Bundesland", "autocomplete": "address-level1"})
    fund_district = StringField("Landkreis", validators=[Optional(), Length(max=100)], render_kw={"placeholder": "Landkreis oder Bezirk (optional)", "autocomplete": "address-level3"})


    # Mantis Details
    gender = SelectField(
        "Entwicklungsstadium/Geschlecht *",
        choices=GENDER_CHOICES,
        validators=[DataRequired(message="Bitte wählen Sie eine Option aus.")],
        render_kw={"title": "Entwicklungsstadium auswählen"}
    )
    location_description = SelectField(
        "Fundortbeschreibung *",
        choices=LOCATION_DESCRIPTION_CHOICES,
        validators=[DataRequired(message="Bitte wählen Sie einen Ortstyp aus.")],
        render_kw={"title": "Fundortbeschreibung auswählen"}
    )
    description = TextAreaField("Details zum Fundort", validators=[Optional(), Length(max=500)], render_kw={"placeholder": "Weitere Details (max. 500 Zeichen)", "rows": 3})

    # Photo Upload
    photo = FileField(
        "Foto (max. 12MB) *",
        validators=[
            FileRequired(message="Ein Foto ist erforderlich."),
            FileAllowed(['jpg', 'jpeg', 'png', 'webp', 'heic', 'heif'], 'Nur Bilddateien (JPG, PNG, WEBP, HEIC, HEIF) sind erlaubt.'),
            FileSize(max_size=12 * 1024 * 1024, message="Das Bild darf maximal 12MB groß sein.")
        ]
    )

    # Honeypot field for spam prevention
    honeypot = StringField(validators=[Optional(), Length(max=1)]) # max=1 is a small defense

    submit = SubmitField("Bericht einreichen")

    def validate_finder_names_dependency(self, extra_validators=None):

        if not self.identical_finder_reporter.data:
            first_name_filled = bool(self.finder_first_name.data)
            last_name_filled = bool(self.finder_last_name.data)

            if first_name_filled and not last_name_filled:
                self.finder_last_name.errors.append('Nachname des Finders ist erforderlich, wenn Vorname angegeben wurde.')
                return False
            if last_name_filled and not first_name_filled:
                self.finder_first_name.errors.append('Vorname des Finders ist erforderlich, wenn Nachname angegeben wurde.')
                return False
        return True
