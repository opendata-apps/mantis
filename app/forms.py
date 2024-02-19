from flask_wtf import FlaskForm
from wtforms.validators import (
    DataRequired,
    Length,
    NumberRange,
    ValidationError,
    InputRequired,
    Optional,
)
from flask_wtf.file import FileAllowed, FileRequired, FileSize
from wtforms import (
    StringField,
    IntegerField,
    DateField,
    SelectField,
    BooleanField,
    FloatField,
    FileField,
    SubmitField,
    validators,
)
from datetime import datetime, timedelta

# translations_cache = {}


def validate_past_date(form, field):
    if field.data:
        if field.data > datetime.today().date():
            raise ValidationError("Das Datum muss heute oder früher sein.")
        elif field.data < datetime.today().date() - timedelta(days=5 * 365):
            raise ValidationError("Das Datum darf nicht älter als 5 Jahre sein.")


def validate_zip_code(form, field):
    if field.data and (len(str(field.data)) > 5 or not str(field.data).isdigit()):
        raise ValidationError(f"Die Postleitzahl ist ungültig. ")


def longLatValidator(form, field):
    if form.longitude.data is None or form.latitude.data is None:
        raise ValidationError("Längen- und Breitengrad sind erforderlich.")

    if form.longitude.data >= form.latitude.data:
        raise ValidationError(
            "Der Breitengrad muss größer als der Längengrad sein (Bitte die Werte tauschen)."
        )


class MantisSightingForm(FlaskForm):
    class Meta:
        locales = ["de_DE", "de"]

    def __init__(self, *args, **kwargs):
        if "LANGUAGES" in kwargs:
            self.LANGUAGES = kwargs.pop("LANGUAGES")
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

    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

    userid = StringField(
        "*Benutzerkennung:", render_kw={"placeholder": "Benutzerkennung"}
    )
    picture = FileField(
        "*Bild laden",
        validators=[
            FileRequired(message="Das Bild ist erforderlich, maximal 10MB."),
            FileAllowed(ALLOWED_EXTENSIONS, message="Nur Bilder sind zulässig!"),
            FileSize(
                max_size=10 * 1024 * 1024, message="Das Bild muss kleiner als 10MB sein"
            ),
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
        validators=[Length(max=500)],
        render_kw={"placeholder": "Freihandeingabe Fundort"},
    )

    longitude = FloatField(
        "*Längengrad",
        validators=[
            InputRequired(
                "Pflichtfeld, das gefüllt wird, \
                           wenn der Marker in der Karte gesetzt ist."
            ),
            longLatValidator,
            NumberRange(min=-180.0, max=180.0),
        ],
        render_kw={
            "placeholder": "z.B. 13.12345",
            "title": "Der Längengrad Ihres Standorts",
        },
        description="Bitte geben Sie den Längengrad des Standorts ein, \
                           an dem Sie die Gottesanbeterin gesehen haben.",
    )

    latitude = FloatField(
        "*Breitengrad",
        validators=[
            InputRequired(
                "Pflichtfeld, das gefüllt wird, \
                          wenn der Marker in der Karte gesetzt ist."
            ),
            NumberRange(min=-90.0, max=90.0),
        ],
        render_kw={
            "placeholder": "z.B. 52.12345",
            "title": "Der Breitengrad Ihres Standorts",
        },
        description="Bitte geben Sie den Breitengrad des Standorts ein, an dem Sie die Gottesanbeterin gesehen haben.",
    )

    zip_code = IntegerField(
        "PLZ",
        validators=[Optional(), validate_zip_code],
        render_kw={"placeholder": "PLZ"},
    )
    city = StringField(
        "*Ort",
        validators=[DataRequired(message="Bitte geben Sie einen Ort ein.")],
        render_kw={"placeholder": "z.B. Berlin"},
    )
    street = StringField(
        "Straße",
        validators=[Optional()],
        render_kw={"placeholder": "z.B. Musterstraße"},
    )
    state = StringField(
        "*Bundesland",
        validators=[DataRequired(message="Das Bundesland ist erforderlich.")],
        render_kw={"placeholder": "Bundesland"},
    )
    district = StringField(
        "Landkreis/Stadtteil", render_kw={"placeholder": "z.B. Mitte"}
    )
    location_description = SelectField(
        "Fundort-Beschreibung",
        choices=location_description_CHOICES,
        default="Keine Angabe",
        render_kw={"title": "Fundort Beschreibung auswählen"},
    )

    report_first_name = StringField(
        "*Vorname (Melder)",
        validators=[DataRequired(message="Der Vorname ist erforderlich.")],
        render_kw={"placeholder": "Erster Buchstabe z.B. M."},
    )
    report_last_name = StringField(
        "*Nachname (Melder)",
        validators=[DataRequired(message="Der Nachname ist erforderlich.")],
        render_kw={"placeholder": "z.B. Mustermann"},
    )
    identical_finder_melder = BooleanField("Finder und Melder sind identisch")
    finder_first_name = StringField(
        "Vorname (Finder)", render_kw={"placeholder": "Erster Buchstabe Finder z.B. M."}
    )
    finder_last_name = StringField(
        "Nachname (Finder)", render_kw={"placeholder": "z.B. Mustermann"}
    )

    sighting_date = DateField(
        "*Funddatum",
        validators=[
            DataRequired(message="Das Funddatum ist erforderlich."),
            validate_past_date,
        ],
        render_kw={"placeholder": "z.B. 2023-05-14"},
    )
    contact = StringField(
        "Kontakt (E-Mail)",
        validators=[
            validators.Optional(),
            validators.Email(
                message="Die Email Adresse ist ungültig.", check_deliverability=True
            ),
        ],
        render_kw={"placeholder": "z.B. max@example.de"},
    )
    honeypot = StringField()
    submit = SubmitField("Absenden")

    def _get_translations(self):
        languages = (
            tuple(self.LANGUAGES) if self.LANGUAGES else (self.meta.locales or None)
        )
        if languages not in translations_cache:
            translations_cache[languages] = get_translations(languages)
        return translations_cache[languages]
