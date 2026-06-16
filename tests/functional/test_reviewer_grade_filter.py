from sqlalchemy import select

from app import db
from app.database.models import TblFundorte
from app.routes.admin import get_filtered_query


def test_low_confidence_filter_selects_only_low(app, session):
    fos = db.session.scalars(select(TblFundorte).limit(2)).all()
    assert len(fos) == 2
    fos[0].geo_grade = "LOW"
    fos[1].geo_grade = "HIGH"
    db.session.commit()

    stmt = get_filtered_query(filter_status="all", confidence="low")
    ids = {m.fundort.id for m in db.session.scalars(stmt).unique()}
    assert fos[0].id in ids
    assert fos[1].id not in ids
