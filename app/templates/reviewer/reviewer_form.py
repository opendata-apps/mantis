from wtforms import Form, BooleanField, StringField, PasswordField, validators

class ReviewerForm(Form):
    userid = StringField("Benutzerkennung: ")
    picture = FileField("Bild", validators=[FileRequired(), FileAllowed(
        ALLOWED_EXTENSIONS, 'Nur Bilder sind zulässig!')])
    gender = SelectField("Entwicklungsstadium",
                         choices=GENDER_CHOICES,
                         default="Bitte auswählen",
                         validators=[DataRequired()])
    picture_description = StringField(
        "Bildbeschreibung", validators=[Length(max=500)])

    longitude = StringField('Längengrad',
                            validators=[InputRequired(),
                                        NumberRange(min=-180.0, max=180.0)])
    latitude = StringField('Breitengrad',
                           validators=[InputRequired(),
                                       NumberRange(min=-90.0, max=90.0)])
    zip_code = IntegerField("PLZ")
    city = StringField("Ort")
    street = StringField("Straße")
    state = StringField("Bundesland")
    district = StringField("Kreis")
    location_description = StringField("Fundort Beschreibung")

    first_name = StringField("Vorname", validators=[DataRequired()])
    last_name = StringField("Name", validators=[DataRequired()])
    sighting_date = DateField("Funddatum")
    contact = StringField("Kontakt (Email/Telefonnummer)",
                          validators=[DataRequired()])
    feedback = BooleanField("Soll Rückmeldung bei Bearbeitung kommen?")

    submit = SubmitField("Absenden")
