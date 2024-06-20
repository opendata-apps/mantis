from app import db
from app.database.aemter_koordinaten import TblAemterCoordinaten
from sqlalchemy import text


def get_amt_full_scan(point):
    try:
        # Create a PostGIS point from the input coordinates
        point_wkt = f"POINT({point[0]} {point[1]} 0)"

        # Use PostGIS ST_Contains for efficient spatial query
        result = (
            db.session.query(TblAemterCoordinaten)
            .filter(
                text(
                    "ST_Contains(ST_Force2D(geom::geometry), ST_GeomFromText(:point, 4326))"
                )
            )
            .params(point=point_wkt)
            .first()
        )

        if result:
            return f"{result.ags} -- {result.gen}"
        else:
            return "No matching Amt found"
    finally:
        db.session.close()


if __name__ == "__main__":
    point = [10.895, 48.3745]
    print(get_amt_full_scan(point))
