""" Tabelle  'aemter' mit Datensätzen
    aus vg5000_gem füllen
"""

import json
import psycopg2
from vg5000_gem import data as jsondata

data = json.loads(jsondata)

conn = psycopg2.connect(
    dbname="mantis_tracker",
    user="mantis_user",
    password="mantis",
    host="localhost"
)
cur = conn.cursor()

for row in data['features']:
    geo = str(row['geometry']).replace("'", '"')
    stm = f"""
    INSERT into aemter (ags, gen, properties)
    VALUES ({row['properties']['AGS']},
           '{row['properties']['GEN']}',
           '{geo}')
    """
    cur.execute(stm)
    conn.commit()
cur.close()
conn.close()
