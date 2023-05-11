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
import os


# Create the form using WTForms
class MantisSightingForm(FlaskForm):
    picture = FileField("Bild", validators=[DataRequired()])
    gender = StringField("Geschlecht")
    picture_description = StringField("Bildbeschreibung")

    longitude = StringField("Längengrad")
    latitude = StringField("Breitengrad")
    zip_code = IntegerField("PLZ")
    city = StringField("Ort")
    street = StringField("Straße")
    country = StringField("Land")
    district = StringField("Kreis")
    location_description = StringField("Fundort Beschreibung")

    first_name = StringField("Vorname", validators=[DataRequired()])
    last_name = StringField("Name", validators=[DataRequired()])
    sighting_date = DateField("Funddatum")
    contact = StringField("Kontakt (Email/Telefonnummer)",
                          validators=[DataRequired()])
    feedback = BooleanField("Soll Rückmeldung bei Bearbeitung kommen?")

    submit = SubmitField("Absenden")
