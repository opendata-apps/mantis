from flask_wtf import FlaskForm
from wtforms.validators import (
    DataRequired,
    Length,
    NumberRange,
    ValidationError,
    InputRequired,
    Optional,
    Email,
)
from flask_wtf.file import FileAllowed, FileRequired, FileSize
from wtforms import (
    StringField,
    DateField,
    SelectField,
    BooleanField,
    FloatField,
    FileField,
    SubmitField,
)
from datetime import datetime, timedelta
import re

def validate_past_date(form, field):
    if field.data:
        today = datetime.today().date()
        if field.data > today:
            raise ValidationError("Das Datum muss heute oder früher sein.")
        elif field.data < today - timedelta(days=5 * 365):
            raise ValidationError("Das Datum darf nicht älter als 5 Jahre sein.")

def validate_zip_code(form, field):
    if field.data:
        if not re.match(r'^\d{5}$', field.data):
            raise ValidationError("Die Postleitzahl muss aus genau 5 Ziffern bestehen.")

def longLatValidator(form, field):
    if form.longitude.data is None or form.latitude.data is None:
        raise ValidationError("Längen- und Breitengrad sind erforderlich.")

    try:
        lon = float(form.longitude.data)
        lat = float(form.latitude.data)
        if lon >= lat:
            raise ValidationError("Der Breitengrad muss größer als der Längengrad sein.")
    except ValueError:
        raise ValidationError("Längen- und Breitengrad müssen gültige Zahlen sein.")

class MantisSightingForm(FlaskForm):
    class Meta:
        locales = ["de_DE", "de"]

    def __init__(self, *args, **kwargs):
        self.LANGUAGES = kwargs.pop("LANGUAGES", None)
        super(MantisSightingForm, self).__init__(*args, **kwargs)
        self.userid = kwargs.pop("userid", None)

    GENDER_CHOICES = [
        ("keine Zuordnung", "Keine Zuordnung"),
        ("Männchen", "Männchen"),
        ("Weibchen", "Weibchen"),
        ("Nymphe", "Nymphe"),
        ("Oothek", "Oothek"),
    ]

    location_description_CHOICES = [
        ("1", "Im Haus"),
        ("2", "Im Garten"),
        ("3", "Auf dem Balkon/auf der Terrasse"),
        ("4", "Am Fenster/an der Hauswand"),
        ("5", "Industriebrache"),
        ("6", "Im Wald"),
        ("7", "Wiese/Weide"),
        ("8", "Heidelandschaft"),
        ("9", "Straßengraben/Wegesrand/Ruderalflur"),
        ("10", "Gewerbegebiet"),
        ("11", "Im oder am Auto"),
        ("99", "anderer Fundort"),
    ]

    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "heic", "heif"}

    userid = StringField(
        "*Benutzerkennung:", 
        validators=[DataRequired(), Length(max=50)],
        render_kw={"placeholder": "Benutzerkennung"}
    )
    picture = FileField(
        "Bild (max. 12MB) *",
        validators=[
            FileRequired(message="Das Bild ist erforderlich, maximal 12MB."),
            FileAllowed(ALLOWED_EXTENSIONS, message="Nur PNG, JPG, JPEG, WEBP, HEIC oder HEIF Bilder sind zulässig!"),
            FileSize(max_size=20 * 1024 * 1024, message="Das Bild muss kleiner als 12MB sein"),
        ],
    )
    gender = SelectField(
        "Entwicklungsstadium/Geschlecht",
        choices=GENDER_CHOICES,
        default="Keine Zuordnung",
        validators=[DataRequired(message="Bitte wählen Sie eine Option.")],
        render_kw={"title": "Entwicklungsstadium auswählen"},
    )
    picture_description = StringField(
        "Sonstige Angaben zum Fundort",
        validators=[Optional(), Length(max=500)],
        render_kw={"placeholder": "Freihandeingabe Fundort"},
    )

    longitude = FloatField(
        "Längengrad *",
        validators=[
            InputRequired("Pflichtfeld, das gefüllt wird, wenn der Marker in der Karte gesetzt ist."),
            longLatValidator,
            NumberRange(min=-180.0, max=180.0, message="Der Längengrad muss zwischen -180 und 180 liegen."),
        ],
        render_kw={
            "placeholder": "z.B. 13.12345",
            "title": "Der Längengrad Ihres Standorts",
        },
    )

    latitude = FloatField(
        "Breitengrad *",
        validators=[
            InputRequired("Pflichtfeld, das gefüllt wird, wenn der Marker in der Karte gesetzt ist."),
            NumberRange(min=-90.0, max=90.0, message="Der Breitengrad muss zwischen -90 und 90 liegen."),
        ],
        render_kw={
            "placeholder": "z.B. 52.12345",
            "title": "Der Breitengrad Ihres Standorts",
        },
    )

    zip_code = StringField(
        "PLZ",
        validators=[Optional(), validate_zip_code],
        render_kw={"placeholder": "PLZ"},
    )
    city = StringField(
        "Ort *",
        validators=[DataRequired(message="Bitte geben Sie einen Ort ein."), Length(max=100)],
        render_kw={"placeholder": "z.B. Berlin"},
    )
    street = StringField(
        "Straße",
        validators=[Optional(), Length(max=100)],
        render_kw={"placeholder": "z.B. Musterstraße"},
    )
    state = StringField(
        "Bundesland *",
        validators=[DataRequired(message="Das Bundesland ist erforderlich."), Length(max=50)],
        render_kw={"placeholder": "Bundesland"},
    )
    district = StringField(
        "Landkreis/Stadtteil", 
        validators=[Optional(), Length(max=100)],
        render_kw={"placeholder": "z.B. Mitte"}
    )
    location_description = SelectField(
        "Fundort-Beschreibung",
        choices=location_description_CHOICES,
        default="Keine Angabe",
        validators=[DataRequired()],
        render_kw={"title": "Fundort Beschreibung auswählen"},
    )

    report_first_name = StringField(
        "Vorname (Melder) *",
        validators=[DataRequired(message="Der Vorname ist erforderlich."), Length(max=50)],
        render_kw={"placeholder": "Erster Buchstabe z.B. M."},
    )
    report_last_name = StringField(
        "Nachname (Melder) *",
        validators=[DataRequired(message="Der Nachname ist erforderlich."), Length(max=50)],
        render_kw={"placeholder": "z.B. Mustermann"},
    )
    identical_finder_melder = BooleanField("Finder und Melder sind identisch")
    finder_first_name = StringField(
        "Vorname (Finder)", 
        validators=[Optional(), Length(max=50)],
        render_kw={"placeholder": "Erster Buchstabe Finder z.B. M."}
    )
    finder_last_name = StringField(
        "Nachname (Finder)", 
        validators=[Optional(), Length(max=50)],
        render_kw={"placeholder": "z.B. Mustermann"}
    )

    sighting_date = DateField(
        "Funddatum *",
        validators=[
            DataRequired(message="Das Funddatum ist erforderlich."),
            validate_past_date,
        ],
        render_kw={"placeholder": "z.B. 2023-05-14"},
    )
    contact = StringField(
        "Kontakt (E-Mail)",
        validators=[
            Optional(),
            Email(message="Die Email Adresse ist ungültig.", check_deliverability=True),
            Length(max=120)
        ],
        render_kw={"placeholder": "z.B. max@example.de"},
    )
    honeypot = StringField('Leave this field empty', validators=[Length(max=0)])
    submit = SubmitField("Absenden")