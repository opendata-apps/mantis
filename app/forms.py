# from flask_wtf import FlaskForm
# from wtforms import StringField, IntegerField, DateField, SelectField
from wtforms.validators import DataRequired, Length
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import IntegerField
from wtforms import DateField
from wtforms import FileField
from wtforms import SubmitField
from wtforms import SelectField
from wtforms import FloatField
from wtforms import BooleanField
from flask_wtf.file import FileAllowed
from flask_wtf.file import FileRequired
from wtforms.validators import InputRequired, NumberRange


# Create the form using WTForms
class MantisSightingForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(MantisSightingForm, self).__init__(*args, **kwargs)
        # add a default argument to pop method
        self.userid = kwargs.pop('userid', None)

    # ? Start Deklaration
    # ? der Auswahlmöglichkeiten einiger Formeingaben
    GENDER_CHOICES = [('keine Zuordnung', 'Keine Zuordnung'),
                      ('männchen', 'Männchen'),
                      ('weibchen', 'Weibchen'),
                      ('nymphen', 'Nymphen'),
                      ('ootheken', 'Ootheken')]

    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'jfif', 'webp'}

    # ? Ende Deklaration

    userid = StringField("Benutzerkennung: ")
    picture = FileField("Bild laden", validators=[FileRequired(), FileAllowed(
        ALLOWED_EXTENSIONS, 'Nur Bilder sind zulässig!')])
    gender = SelectField("Entwicklungsstadium",
                         choices=GENDER_CHOICES,
                         default="Bitte auswählen",
                         validators=[DataRequired()])
    picture_description = StringField(
        "Bildbeschreibung", validators=[Length(max=500)])

    longitude = FloatField('Längengrad',
                           validators=[InputRequired(),
                                       NumberRange(min=-180.0, max=180.0)])
    latitude = FloatField('Breitengrad',
                          validators=[InputRequired(),
                                      NumberRange(min=-90.0, max=90.0)])
    zip_code = IntegerField("PLZ")
    city = StringField("Ort")
    street = StringField("Straße")
    state = StringField("Bundesland")
    district = StringField("Kreis")
    location_description = StringField("Fundort Beschreibung")

    report_first_name = StringField("Vorname", validators=[DataRequired()])
    report_last_name = StringField("Name", validators=[DataRequired()])
    identical_finder_melder = BooleanField("Finder und Melder sind identisch")
    finder_first_name = StringField("Vorname")
    finder_last_name = StringField("Name")
    sighting_date = DateField("Funddatum")
    contact = StringField("Kontakt (Email/Telefonnummer)",
                          validators=[DataRequired()])

    submit = SubmitField("Absenden")
