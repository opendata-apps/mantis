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


def parse_date(date_value, formats):
    if isinstance(date_value, datetime):
        return date_value.date()

    if isinstance(date_value, float) or date_value == "???" or date_value == "nachgehakt" or date_value == "01.09,2021" or date_value == "NaT" or date_value == "nat":
        return None

    for fmt in formats:
        try:
            return datetime.strptime(str(date_value), fmt).date()
        except ValueError:
            pass

    return None


date_formats = [
    '%Y-%m-%d %H:%M:%S',
    '%d.%m.%Y',
]


def get_osm_id(session, plz, ort):
    plzort = session.query(TblPlzOrt).filter_by(plz=plz, ort=ort).first()
    if plzort:
        return plzort.osm_id
    return None


def process_fundorte_longitude(row):
    longitude = row['Länge Ost']
    return process_nan(longitude)


def process_fundorte_latitude(row):
    latitude = row['Breite Nord']
    return process_nan(latitude)


def process_anzahl(value):
    if pd.isna(value):
        return 0

    if isinstance(value, str):
        try:
            int_value = int("".join(filter(str.isdigit, value)))
        except ValueError:
            int_value = 0
        return int_value
    elif isinstance(value, (int, float)):
        return int(value)
    else:
        return 0


def truncate_string(value, max_length):
    if value is not None:
        return str(value)[:max_length]
    return value


# Modify process_nan to use the given default value for non-numeric types
def process_nan(value, default_value=None):
    if isinstance(value, float) and math.isnan(value):
        return default_value
    return value


database_uri = "postgresql://postgres:postgres@localhost/mantis_tracker"
engine = create_engine(database_uri)

Session = sessionmaker(bind=engine)
session = Session()

path_to_excel_file = "app\database\Mantis_DB_2021_Meldungen_20220812_ZIT.xlsx"

df = pd.read_excel(path_to_excel_file)

for index, row in df.iterrows():
    try:
        meldung = TblMeldungen(
            dat_fund=parse_date(row['Funddatum'], date_formats),
            dat_meld=parse_date(row['Meldedatum'], date_formats),
            dat_bear=parse_date(row['Meldedatum'], date_formats),
            anzahl=process_anzahl(row['Gesamtzahl an Tieren (Spalte M+N+O)']),
            fo_quelle=row['Fundquelle'],
            fo_kategorie="M",
            anmerkung=row['Bemerkungen']
        )

        fundort_beschreibung = TblFundortBeschreibung(
            beschreibung=row['Habitats-/Fundbemerkung']
        )

        osm_id = get_osm_id(session, row['PLZ laut google'], row['Fundort_1 '])
        if osm_id is None:
            print(
                f"Error processing row {index}: No osm_id found for plz {row['PLZ laut google']} and ort {row['Fundort_1 ']}. Skipping.")
            continue

        fundorte = TblFundorte(
            plz=row['PLZ laut google'],
            ort=osm_id,
            strasse=row['Fundort_2'],
            land=row['Land'],
            kreis=row['Kreis'],
            beschreibung=row['Habitats-/Fundbemerkung'],
            longitude=process_fundorte_longitude(row),
            latitude=process_fundorte_latitude(row),
            ablage=row['Ordner (hier befindet sich die E-Mail und das Foto chronologisch nach Meldedatum)']
        )

        user = TblUsers(
            user_id=row['Finder'],
            user_name=row['Finder'],
            user_rolle="R",
            user_kontakt=row['Melder Adresse (für Rückfragen)']
        )

        session.add(meldung)
        session.add(fundort_beschreibung)
        session.flush()  # Get the newly created IDs

        fundorte.beschreibung = fundort_beschreibung.id

        session.add(fundorte)
        session.add(user)
        session.flush()  # Get the newly created IDs

        meldung_user = TblMeldungUser(
            id_meldung=meldung.id,
            id_user=user.id
        )

        session.add(meldung_user)
        session.commit()
    except Exception as e:
        print(f"Error processing row {index}: {e}")
        session.rollback()
        continue

# Close the session
session.close()

print("Data imported successfully!")
