# Before running this script, make sure to install the following packages:
# pip install psycopg2-binary
# pip install geoalchemy2
# apt/dnf/... install  postgis


import json
import psycopg2
from vg5000_gem import data as jsondata

data = json.loads(jsondata)

conn = psycopg2.connect(
    dbname="mantis_tracker", user="postgres", password="postgres", host="localhost"
)
conn.autocommit = True  # Set autocommit to True for creating extensions
cur = conn.cursor()

# Enable PostGIS extension
cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

# Create the table with a 3D geometry column that can handle both Polygon and MultiPolygon
cur.execute(
    """
    CREATE TABLE IF NOT EXISTS aemter (
        ags VARCHAR PRIMARY KEY,
        gen VARCHAR,
        geom GEOMETRY(GEOMETRYZ, 4326)
    )
"""
)

conn.autocommit = False  # Set autocommit back to False for data insertion

for row in data['features']:
    geo = json.dumps(row["geometry"])
    stm = """
    INSERT INTO aemter (ags, gen, geom)
    VALUES (%s, %s, ST_Force3D(ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326))))
    ON CONFLICT (ags) DO NOTHING
    """
    cur.execute(stm, (row["properties"]["AGS"], row["properties"]["GEN"], geo))
    conn.commit()

cur.close()
conn.close()

print("Data insertion completed successfully!")
