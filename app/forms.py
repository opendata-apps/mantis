from app.database.models import TblMeldungen, TblFundortBeschreibung, TblFundorte, TblMeldungUser, TblPlzOrt, TblUsers
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, DateField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Optional


def plz_choices():
    plz_list = TblPlzOrt.query.all()
    return [(plz.osm_id, plz.plz) for plz in plz_list]


class ReportMantisReligiosaForm(FlaskForm):
    dat_fund = DateField("Date of finding", validators=[DataRequired()])
    anzahl = IntegerField("Number of mantis", validators=[Optional()])
    plz = StringField("Postal Code", validators=[
                      DataRequired(), Length(max=5)])
    ort = StringField("City", validators=[DataRequired()])
    strasse = StringField("Street", validators=[
                          DataRequired(), Length(max=100)])
    land = StringField("Country", validators=[DataRequired(), Length(max=50)])
    kreis = StringField("District", validators=[DataRequired()])
    beschreibung = SelectField("Description", choices=plz_choices())
    longitude = StringField("Longitude", validators=[
                            DataRequired(), Length(max=25)])
    latitude = StringField("Latitude", validators=[
                           DataRequired(), Length(max=25)])
    ablage = StringField("Ablage", validators=[
                         DataRequired(), Length(max=255)])
    anmerkung = TextAreaField(
        "Notes", validators=[Optional(), Length(max=500)])
    user_name = StringField("User Name", validators=[
                            DataRequired(), Length(max=45)])
    user_kontakt = StringField("User Contact", validators=[
                               Optional(), Length(max=45)])
