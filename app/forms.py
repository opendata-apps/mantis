from app.database.models import TblMeldungen, TblFundortBeschreibung, TblFundorte, TblMeldungUser, TblPlzOrt, TblUsers
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DateField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Optional
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DateField, FileField, SubmitField, BooleanField
from wtforms.validators import DataRequired
from werkzeug.utils import secure_filename
from flask_wtf.file import FileAllowed, FileRequired
from flask_wtf import FlaskForm
from wtforms import FileField
from wtforms import Form, StringField
from wtforms.validators import InputRequired, NumberRange
import os


# Create the form using WTForms
class MantisSightingForm(FlaskForm):
    # ? Start Deklaration
    # ? der Auswahlmöglichkeiten einiger Formeingaben
    GENDER_CHOICES = [('', 'Bitte auswählen'),
                      ('männchen', 'Männchen'),
                      ('weibchen', 'Weibchen'),
                      ('nymphen', 'Nymphen'),
                      ('ootheken', 'Ootheken')]

    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # ? Ende Deklaration

    picture = FileField("Bild", validators=[FileRequired(), FileAllowed(
        ALLOWED_EXTENSIONS, 'Nur Bilder sind zulässig!')])
    gender = SelectField("Entwicklungsstadium", choices=GENDER_CHOICES,
                         default="Bitte auswählen", validators=[DataRequired()])
    picture_description = StringField(
        "Bildbeschreibung", validators=[Length(max=500)])

    longitude = StringField('Längengrad', validators=[InputRequired(), NumberRange(min=-180.0, max=180.0)])
    latitude = StringField('Breitengrad', validators=[InputRequired(), NumberRange(min=-90.0, max=90.0)])
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
