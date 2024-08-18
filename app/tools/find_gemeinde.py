import json
from shapely.geometry import shape, Point
from app.config import Config
from sqlalchemy import create_engine
from sqlalchemy import text

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)


def get_amt_full_scan(point):
    with engine.connect() as conn:
        stm = "select * from aemter"
        rows = conn.execute(text(stm))
        for row in rows:
            try:
                coords = json.loads(row[2])
            except json.JSONDecodeError:
                cleaned_coords = row[2].replace("'", '"').replace('None', 'null')
                try:
                    coords = json.loads(cleaned_coords)
                except json.JSONDecodeError:
                    continue
            polygon = shape(coords)
            point_obj = Point(point)
            inside = polygon.contains(point_obj)
            if inside:
                ags = row[0]
                gem = row[1]
                # add leading zero
                if ags < 10000000:
                    return f"0{ags} -- {gem}"
                else:
                    return f"{ags} -- {gem}"
    return None


if __name__ == '__main__':
    SQLALCHEMY_DATABASE_URI = 'postgresql://mantis_user:mantis@localhost/mantis_tracker'
    engine = create_engine(SQLALCHEMY_DATABASE_URI)

    point = [12.07906, 51.3324]
    point = [10.895, 48.3745]

    print(get_amt_full_scan(point))
