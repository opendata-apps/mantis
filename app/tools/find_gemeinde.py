import json
from shapely.geometry import shape, Point
from sqlalchemy import text
from app import db


def get_amt_full_scan(point):
    with db.engine.connect() as conn:
        stm = "select * from aemter"
        rows = conn.execute(text(stm))
        for row in rows:
            try:
                # Handle both string and dict formats for properties column
                if isinstance(row[2], dict):
                    coords = row[2]
                else:
                    coords = json.loads(str(row[2]).replace("'", '"'))
                
                # Skip if no geometry data
                if not coords or 'type' not in coords or 'coordinates' not in coords:
                    continue
                    
                polygon = shape(coords)
                point_geom = Point(point)
                inside = polygon.contains(point_geom)
                if inside:
                    ags = row[0]
                    gem = row[1]
                    # add leading zero
                    if ags < 10000000:
                        return f"0{ags} -- {gem}"
                    else:
                        return f"{ags} -- {gem}"
            except Exception:
                # Skip malformed geometry data
                continue


if __name__ == '__main__':

    point = [12.07906, 51.3324]
    point = [10.895, 48.3745]

    print(get_amt_full_scan(point))
