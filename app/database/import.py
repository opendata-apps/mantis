from datetime import date
import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from app.database.models import TblMeldungen, TblFundortBeschreibung, TblFundorte, TblMeldungUser, TblPlzOrt, TblUsers
from flask_sqlalchemy import SQLAlchemy
import math
from datetime import datetime
import random
from datetime import timedelta
import random as rand

default_date = datetime.date(datetime(1900, 1, 1))
# replace with your database credentials (username, password, address)
DATABASE_URL = 'postgresql://postgres:postgres@localhost/mantis_tracker'

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()


def parse_date(date_value, default_date=None):
    if isinstance(date_value, str):
        try:
            return datetime.strptime(date_value, "%d.%m.%Y").date()
        except ValueError:
            return default_date
    elif isinstance(date_value, datetime):
        return date_value.date()
    else:
        return default_date


file_path = 'app\database\Mantis_DB_2021_Meldungen_20220812_ZIT.xlsx'
sheet_name = 'Meldungen 2021'  # Modify this to match sheet name in your excel file

df = pd.read_excel(file_path, sheet_name=sheet_name)
session.commit()

for index, row in df.iterrows():
    dat_fund = parse_date(row['Funddatum'])
    dat_meld = parse_date(row['Meldedatum'])
    dat_bear = parse_date(row['Erstbearbeitung am'])

    # Replace 'NaT' values with None
    if pd.isnull(dat_meld):
        dat_meld = default_date
    if pd.isnull(dat_bear):
        dat_bear = default_date
    if pd.isnull(dat_fund):
        dat_fund = default_date

    fo_quelle = row['Fundquelle']
    if not isinstance(fo_quelle, str) or len(fo_quelle) != 1:
        fo_quelle = '?'

    fo_kategorie = row['Fundort_1 ']
    if not isinstance(fo_kategorie, str) or len(fo_kategorie) != 1:
        fo_kategorie = '?'

    anzahl = row['Gesamtzahl an Tieren (Spalte M+N+O)']
    if pd.isna(anzahl):
        anzahl = None

    meldung = TblMeldungen(
        dat_fund=dat_fund,
        dat_meld=dat_meld,
        dat_bear=dat_bear,
        anzahl=anzahl,
        fo_zuordung=None,  # I couldn't find which column is related to fo_zuordung
        fo_quelle=fo_quelle,
        fo_kategorie=fo_kategorie,
        anmerkung=row['Bemerkungen']
    )

    session.add(meldung)
    session.commit()

    plz = str(row['PLZ laut google'])[2:]
    plz_ort_row = session.query(TblPlzOrt).filter_by(plz=plz).first()

    if plz_ort_row:
        kreis = plz_ort_row.landkreis
    else:
        kreis = row['Kreis']
try:
    fundort = TblFundorte(
        plz=plz,
        ort=row['Fundort_1 '][:50],
        strasse=row['Fundort_2'],
        land=row['Land'][50:],
        kreis=kreis[50:],
        # I couldn't find which column is related to beschreibung
        beschreibung="2",
        longitude=row['Länge Ost'],
        latitude=row['Breite Nord'],
        ablage="?"
    )

    session.add(fundort)
    session.commit()
except ValueError:
    print("ValueError")
    pass

    user = session.query(TblUsers).filter_by(user_name=row['Melder']).first()
    if not user:
        user = TblUsers(
            user_id=rand.randint(1, 100000),
            user_name=row['Melder'],
            user_rolle='?',  # I couldn't find which column is related to user_rolle
            user_kontakt=row['Melder Adresse (für Rückfragen)'],
        )

        session.add(user)
        session.commit()

    melduser = TblMeldungUser(
        id_meldung=meldung.id,
        id_user=user.id
    )

    session.add(melduser)
    session.commit()
    print("Done")
