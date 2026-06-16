from datetime import datetime, timezone

from sqlalchemy import select

from app import db
from app.database.models import TblFundorte


def test_grade_fundorte_backfill_sets_grade(app, session, monkeypatch):
    from app.tools import geo_grade_service as svc

    monkeypatch.setattr(
        svc,
        "grade_fundort_fields",
        lambda lat, lon, land, kreis, ort: {
            "geo_grade": "HIGH",
            "geo_confidence": 0.95,
            "geo_matched_level": "ORTSTEIL",
            "geo_reasons": ["x"],
            "geo_graded_at": datetime.now(timezone.utc),
        },
    )
    fo = db.session.scalar(select(TblFundorte).limit(1))
    fo.geo_grade = None
    db.session.commit()

    res = app.test_cli_runner().invoke(args=["grade-fundorte", "--only-ungraded"])
    assert res.exit_code == 0, res.output
    db.session.refresh(fo)
    assert fo.geo_grade == "HIGH"
