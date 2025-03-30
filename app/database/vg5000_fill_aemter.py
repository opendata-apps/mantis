""" Tabelle  'aemter' mit Datensätzen
    aus vg5000_gem füllen
"""

import json
from app.database.vg5000_gem import data as jsondata
from sqlalchemy import text
import sqlalchemy.orm as orm


def import_aemter_data(db, jsondata):

    data = json.loads(jsondata)

    # Create a session
    Session = orm.sessionmaker(bind=db)
    session = Session()

    for row in data['features']:
        geo = str(row['geometry']).replace("'", '"')
        stm = f"""
        INSERT into aemter (ags, gen, properties)
        VALUES ({row['properties']['AGS']},
                '{row['properties']['GEN']}',
                '{geo}')"""
        session.execute(text(stm))
    
    session.commit()
    session.close()
