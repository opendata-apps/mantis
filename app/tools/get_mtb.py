import http.client
import os
import psycopg2
from dotenv import load_dotenv
load_dotenv('/absolute/path/to/.env')
mdb = os.environ.get("mdb")
muser = os.environ.get("muser")
mpass = os.environ.get("mpass")


def get_mtb(lat, lon):
    """Function to retrieve MTB using latitude and longitude.

    This script could run as a cronjob

    0 * * * * .../venv/bin/python3 .../app/tools/get_mtb.py

    """

    conn = http.client.HTTPSConnection("susudata.de")
    payload = ""
    headers = {'Origin': "https://susudata.de"}
    conn.request("POST", f"/tk25/tiles?lat={lat}&lon={lon}&zoom=12",
                 payload, headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
    # Assuming the first word is always the MTB ID
    mtb_id = data.split()[0]
    return mtb_id


if __name__ == '__main__':
    credentials = f"host=localhost dbname={mdb} user={muser} password={mpass}"
    conn = psycopg2.connect(credentials)
    cur = conn.cursor()
    sql = 'select id, longitude, latitude from fundorte where mtb is NULL'
    cur.execute(sql)
    all = cur.fetchall()
    for row in all[:10]:
        mtb = get_mtb(row[2], row[1])
        upd = f"update fundorte set mtb='{mtb}' where id={row[0]}"
        cur.execute(upd)
    conn.commit()
