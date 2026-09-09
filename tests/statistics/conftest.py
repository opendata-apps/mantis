from datetime import date

import pytest
from sqlalchemy import select

from app.database.models import TblMeldungen


@pytest.fixture
def counted_reports(session):
    reports = session.scalars(
        select(TblMeldungen).order_by(TblMeldungen.id).limit(3)
    ).all()
    # Two approved regions with different counts, plus a large unapproved report.
    for report, ags, status, counts in zip(
        reports,
        ["11000001", "12062001", "11000001"],
        ["APPR", "APPR", "OPEN"],
        [(1, 2, 3, 4, 5), (2, 0, 0, 0, 0), (100, 100, 100, 100, 100)],
        strict=True,
    ):
        report.dat_meld = report.dat_fund_von = date(1992, 6, 10)
        report.fundort.amt = ags
        report.fundort.mtb = "3446"
        report.statuses = [status]
        report.art_m, report.art_w, report.art_n, report.art_o, report.art_f = counts
        report.tiere = sum(counts)
    session.commit()
