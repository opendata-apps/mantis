from wtforms import Form
from wtforms import BooleanField
from wtforms import StringField
from wtforms import PasswordField
from wtforms import validators
from wtforms import IntegerField
from wtforms import DateField
from wtforms import SubmitField

class ReviewerForm(Form):
    user_id = StringField("Benutzerkennung: ")

    longitude = StringField('Längengrad')
#                            validators=[InputRequired(),
#                                        NumberRange(min=-180.0, max=180.0)])
    latitude = StringField('Breitengrad')
#                           validators=[InputRequired(),
#                                       NumberRange(min=-90.0, max=90.0)])
    zip_code = IntegerField("PLZ")
    city = StringField("Ort")
    street = StringField("Straße")
    state = StringField("Bundesland")
    district = StringField("Kreis")
    location_description = StringField("Fundort Beschreibung")

    first_name = StringField("Vorname")#, validators=[DataRequired()])
    last_name = StringField("Name")#, validators=[DataRequired()])
    sighting_date = DateField("Funddatum")
    contact = StringField("Kontakt (Email/Telefonnummer)")#,
#                          validators=[DataRequired()])
    feedback = BooleanField("Soll Rückmeldung bei Bearbeitung kommen?")

    submit = SubmitField("Absenden")
