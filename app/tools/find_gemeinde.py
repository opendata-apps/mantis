import json
import psycopg2
from shapely.geometry import shape, Point


def get_amt_full_scan(point):
    conn = psycopg2.connect(
        dbname="mantis_tracker",
        user="mantis_user",
        password="mantis",
        host="localhost"
    )
    cur = conn.cursor()

    stm = "select * from aemter"
    cur.execute(stm)
    rows = cur.fetchall()
    for row in rows:
        coords = json.loads(str(row[2]).replace("'", '"'))
        polygon = shape(coords)
        point = Point(point)
        inside = polygon.contains(point)
        if inside:
            ags = row[0]
            gem = row[1]
            cur.close()
            conn.close()
            return f"{ags} -- {gem}"


if __name__ == '__main__':

    point = [12.07906, 51.3324]
    point = [10.895, 48.3745]
    print(get_amt_full_scan(point))
