from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Length, NumberRange, Email, ValidationError, InputRequired, Optional, Regexp
from flask_wtf.file import FileAllowed, FileRequired, FileSize
from wtforms import StringField, IntegerField, DateField, SelectField, BooleanField, FloatField, FileField, SubmitField
from datetime import date
import re

# translations_cache = {}


def validate_past_date(form, field):
    if field.data and field.data > date.today():
        raise ValidationError("Das Datum muss heute oder früher sein.")


def validate_zip_code(form, field):
    if field.data and (len(str(field.data)) > 5 or not str(field.data).isdigit()):
        raise ValidationError(
            f"Die Postleitzahl ist ungültig: {len(str(field.data))}")


class MantisSightingForm(FlaskForm):
    class Meta:
        locales = ['de_DE', 'de']

    def __init__(self, *args, **kwargs):
        if 'LANGUAGES' in kwargs:
            self.LANGUAGES = kwargs.pop('LANGUAGES')
        super(MantisSightingForm, self).__init__(*args, **kwargs)
        self.userid = kwargs.pop('userid', None)

    GENDER_CHOICES = [('keine Zuordnung', 'Keine Zuordnung'),
                      ('männchen', 'Männchen'),
                      ('weibchen', 'Weibchen'),
                      ('nymphen', 'Nymphen'),
                      ('ootheken', 'Ootheken')]

    location_description_CHOICES = [('keine Angabe', 'Keine Angabe'),
                                    ('im Haus', 'Im Haus'),
                                    ('im Garten', 'Im Garten'),
                                    ('auf dem Balkon/auf der Terrasse',
                                     'Auf dem Balkon/auf der Terrasse'),
                                    ('am Fenster/an der Hauswand',
                                     'Am Fenster/an der Hauswand'),
                                    ('Industriebrache', 'Industriebrache'),
                                    ('im Wald', 'Im Wald'),
                                    ('Wiese/Weide', 'Wiese/Weide'),
                                    ('Heidelandschaft', 'Heidelandschaft'),
                                    ('Straßengraben/Wegesrand/Ruderalflur',
                                     'Straßengraben/Wegesrand/Ruderalflur'),
                                    ('Gewerbegebiet', 'Gewerbegebiet'),
                                    ('Im oder am Auto', 'Im oder am Auto')]

    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'jfif', 'webp'}

    userid = StringField("*Benutzerkennung:", render_kw={
                         'placeholder': 'Benutzerkennung'})
    picture = FileField("*Bild laden", validators=[
        FileRequired(message='Das Bild ist erforderlich, maximal 10MB.'),
        FileAllowed(ALLOWED_EXTENSIONS, message='Nur Bilder sind zulässig!'),
        FileSize(max_size=10*1024*1024,
                 message='Das Bild muss kleiner als 10MB sein')
    ])
    gender = SelectField("Entwicklungsstadium/Geschlecht",
                         choices=GENDER_CHOICES,
                         default="Keine Zuordnung",
                         validators=[DataRequired(
                             message="Bitte wählen Sie eine Option.")],
                         render_kw={'title': 'Entwicklungsstadium auswählen'})
    picture_description = StringField(
        "Sonstige Angaben zum Fundort",
        validators=[Length(max=500)],
        render_kw={'placeholder': 'Freihandeingabe Fundort'})

    longitude = FloatField('*Längengrad',
                           validators=[InputRequired('Pflichtfeld, das gefüllt wird, \
                           wenn der Marker in der Karte gesetzt ist.'),
                                       NumberRange(min=-180.0, max=180.0)],
                           render_kw={'placeholder': 'z.B. 13.12345',
                                      'title': 'Der Längengrad Ihres Standorts'},
                           description='Bitte geben Sie den Längengrad des Standorts ein, \
                           an dem Sie die Mantis religiosa gesehen haben.')

    latitude = FloatField('*Breitengrad',
                          validators=[InputRequired('Pflichtfeld, das gefüllt wird, \
                          wenn der Marker in der Karte gesetzt ist.'),
                                      NumberRange(min=-90.0, max=90.0)],
                          render_kw={'placeholder': 'z.B. 52.12345',
                                     'title': 'Der Breitengrad Ihres Standorts'},
                          description='Bitte geben Sie den Breitengrad des Standorts ein, an dem Sie die Mantis religiosa gesehen haben.')
    zip_code = IntegerField("PLZ", validators=[Optional()], render_kw={
                            'placeholder': 'PLZ'})
    city = StringField("*Ort", validators=[DataRequired(message='Bitte geben Sie einen Ort ein.')], render_kw={
                       'placeholder': 'z.B. Berlin'})
    street = StringField("Straße", validators=[Optional()], render_kw={
                         'placeholder': 'z.B. Musterstraße'})
    state = StringField("*Bundesland", validators=[DataRequired(message='Das Bundesland ist erforderlich.')], render_kw={
                        'placeholder': 'Bundesland'})
    district = StringField("Landkreis/Stadtteil", render_kw={'placeholder': 'z.B. Mitte'})
    location_description = SelectField("Fundort-Beschreibung", choices=location_description_CHOICES,
                                       default="Keine Angabe", render_kw={'title': 'Fundort Beschreibung auswählen'})

    report_first_name = StringField(
        "*Vorname (Melder)", validators=[DataRequired(message='Der Vorname ist erforderlich.')], render_kw={'placeholder': 'Erster Buchstabe z.B. M.'})
    report_last_name = StringField(
        "*Nachname (Melder)", validators=[DataRequired(message='Der Nachname ist erforderlich.')], render_kw={'placeholder': 'z.B. Mustermann'})
    identical_finder_melder = BooleanField("Finder und Melder sind identisch")
    finder_first_name = StringField(
        "Vorname (Finder)", render_kw={'placeholder': 'Erster Buchstabe Finder z.B. M.'})
    finder_last_name = StringField(
        "Nachname (Finder)", render_kw={'placeholder': 'z.B. Mustermann'})

    sighting_date = DateField("*Funddatum", validators=[
                              DataRequired(message='Das Funddatum ist erforderlich.'), validate_past_date], render_kw={'placeholder': 'z.B. 2023-05-14'})
    contact = StringField("Kontakt (E-Mail)", validators=[Optional(Email(message='Die Email Adresse ist ungültig.'))],
                          render_kw={'placeholder': 'z.B. max@example.de'})

    submit = SubmitField("Absenden")

    def _get_translations(self):
        languages = tuple(self.LANGUAGES) if self.LANGUAGES else (
            self.meta.locales or None)
        if languages not in translations_cache:
            translations_cache[languages] = get_translations(languages)
        return translations_cache[languages]
