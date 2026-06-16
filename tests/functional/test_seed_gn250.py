from unittest.mock import patch

from sqlalchemy import func, select

from app import db
from app.database.models import TblGeoNames

_ROWS = [
    {
        "name": "Schadewitz",
        "longitude": 13.52,
        "latitude": 51.58,
        "ags": 12062264,
        "kreis": "Elbe-Elster",
    },
    {
        "name": "Schönborn",
        "longitude": 13.55,
        "latitude": 51.60,
        "ags": 12062264,
        "kreis": "Elbe-Elster",
    },
]


def test_seed_gn250_inserts_rows(app, session):
    runner = app.test_cli_runner()
    with patch("app.cli.fetch_geonames", return_value=_ROWS):
        res = runner.invoke(args=["seed-gn250"])
    assert res.exit_code == 0, res.output
    count = db.session.scalar(select(func.count(TblGeoNames.id)))
    assert count == 2
    names = set(db.session.scalars(select(TblGeoNames.name)))
    assert {"Schadewitz", "Schönborn"} <= names
