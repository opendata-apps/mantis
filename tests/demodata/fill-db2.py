"""
Fill sample data into the database.
The image is not visible because of a
static not existing imagepath
"""

from app import db
from random import choice
from faker import Faker
from app.database.models import TblFundorte
from app.database.models import TblMeldungen
from app.database.models import TblMeldungUser
from app.database.models import TblUsers
from app.tools.gen_user_id import get_new_id
from app import create_app

app = create_app()
fake = Faker("de_DE")


def _set_gender_fields(selected_gender):
    genders = {"art_m": 0, "art_w": 0, "art_n": 0, "art_o": 0}
    gender_mapping = {
        "Männchen": "art_m",
        "Weibchen": "art_w",
        "Nymphe": "art_n",
        "Oothek": "art_o",
    }
    gender_field = gender_mapping.get(selected_gender)

    if gender_field:
        genders[gender_field] = 1

    return genders


def generate_sample_reports():
    genders = ["Männchen", "Weibchen", "Nymphe", "Oothek"]

    with app.app_context():
        for _ in range(600):
            usrid = get_new_id()
            finderid = get_new_id()

            user = TblUsers(
                user_id=usrid,
                user_name=fake.last_name() + " " + fake.first_name()[0] + ".",
                user_rolle=1,
                user_kontakt=fake.email(),
            )
            db.session.add(user)

            # Simulating finder user creation like in the real route
            finder = TblUsers(
                user_id=finderid,
                user_name=fake.last_name() + " " + fake.first_name()[0] + ".",
                user_rolle=2,
            )
            db.session.add(finder)

            # Simulating the file upload path
            imagepath = "2023/2023-01-19/Trebbin_OT_Kleinbeuthen-"
            imagepath += "20230803203653-e99986104029a483763138a3"
            imagepath += "0385a1c77bfc5b57.webp"
            new_fundort = TblFundorte(
                plz=fake.postcode(),
                ort=fake.city(),
                strasse=fake.street_name(),
                kreis=fake.city_suffix(),
                land=fake.state(),
                longitude=str(fake.coordinate(center=10.4515, radius=2.5)),  # Approximate center of Germany
                latitude=str(fake.coordinate(center=51.1657, radius=2.5)),   # Approximate center of Germany
                beschreibung="1",
                ablage=imagepath,
            )
            db.session.add(new_fundort)
            db.session.flush()

            gender_fields = _set_gender_fields(choice(genders))

            new_meldung = TblMeldungen(
                dat_fund_von=fake.date_time_this_decade(),
                dat_meld=fake.date_time_this_month(),
                fo_zuordnung=new_fundort.id,
                fo_quelle="F",
                art_f="0",
                tiere="1",
                **gender_fields,
                anm_melder=fake.text()
            )
            db.session.add(new_meldung)
            db.session.flush()

            new_meldung_user = TblMeldungUser(
                id_meldung=new_meldung.id, id_user=user.id, id_finder=finder.id
            )

            db.session.add(new_meldung_user)
            db.session.commit()

    print("Sample reports created!")


if __name__ == '__main__':
    import sys
    import os
    from pathlib import Path
    approot = Path(os.path.dirname(os.path.abspath(__file__)))
    mantisstart = approot.parent.parent
    sys.path.append(str(mantisstart))
    generate_sample_reports()
