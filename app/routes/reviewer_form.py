from wtforms import (BooleanField, DateField, Form, IntegerField,
                     StringField, SubmitField)


class ReviewerForm(Form):
    css_input_field = """bg-gray-50 border border-gray-300 text-gray-900
    text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500
    block p-2.5 dark:bg-gray-700 dark:border-gray-600
    dark:placeholder-gray-400 dark:text-white
    dark:focus:ring-blue-500 dark:focus:border-blue-500"""
    user_id = StringField("Benutzerkennung: ",
                          render_kw={'style': 'width:350px',
                                     'class': css_input_field})
    longitude = StringField('Längengrad',
                            render_kw={'class': css_input_field + "w-32"})
    latitude = StringField('Breitengrad',
                           render_kw={'class': css_input_field})
    user_name = StringField("Name (Melder)",
                            render_kw={'class': css_input_field + "w-80"})
    art_w = StringField("Anzahl (weiblich)",
                        render_kw={'style': 'width:50px',
                                   'class': css_input_field})
    art_m = StringField("Anzahl (männlich)",
                        render_kw={'style': 'width:50px',
                                   'class': css_input_field})
    art_n = StringField("Anzahl (Nymphe)",
                        render_kw={'style': 'width:50px',
                                   'class': css_input_field})
    art_o = StringField("Anzahl (Oothek)",
                        render_kw={'style': 'width:50px',
                                   'class': css_input_field})
    zip_code = IntegerField("PLZ")
    city = StringField("Ort")
    street = StringField("Straße")
    state = StringField("Bundesland")
    district = StringField("Kreis")
    location_description = StringField("Fundort-Beschreibung")

    first_name = StringField("Vorname")  # , validators=[DataRequired()])
    last_name = StringField("Name")  # , validators=[DataRequired()])
    sighting_date = DateField("Funddatum")
    contact = StringField("Kontakt (E-Mail/Telefonnummer)")  # ,
#                          validators=[DataRequired()])
    feedback = BooleanField("Soll Rückmeldung bei Bearbeitung kommen?")

    submit = SubmitField("Absenden")
