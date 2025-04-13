""" Tabelle  'aemter' mit Datensätzen
    aus vg5000_gem füllen
"""

import json
from app.database.vg5000_gem import data as jsondata
from sqlalchemy import text
import sqlalchemy.orm as orm
import click


def import_aemter_data(db, jsondata):

    data = json.loads(jsondata)

    # Create a session
    Session = orm.sessionmaker(bind=db)
    session = Session()

    for row in data['features']:
        ags = row['properties']['AGS']
        gen = row['properties']['GEN']
        
        # Check if record with this AGS already exists
        check_stm = f"SELECT ags FROM aemter WHERE ags = {ags}"
        existing = session.execute(text(check_stm)).fetchone()
        
        if not existing:
            geo = str(row['geometry']).replace("'", '"')
            stm = f"""
            INSERT into aemter (ags, gen, properties)
            VALUES ({ags},
                    '{gen}',
                    '{geo}')"""
            session.execute(text(stm))
        else:
            return
    
    session.commit()
    session.close()
