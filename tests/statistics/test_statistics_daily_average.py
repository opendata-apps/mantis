import json
import re
from datetime import date

import pytest

from app.database.models import TblFundorte, TblMeldungen


@pytest.fixture
def hourly_reports(session):
    # The directory date and hyphenated city must not override the image timestamp.
    for index, (timestamp, status, ags, found) in enumerate(
        [
            ("19910719003000", "APPR", "12000000", date(1991, 7, 19)),
            ("19910719011500", "APPR", "12000000", date(1991, 7, 19)),
            ("19910719014500", "APPR", "12000000", date(1991, 7, 19)),
            ("19910719235900", "APPR", "11000000", date(1991, 7, 19)),
            ("19910719140000", "OPEN", "12000000", date(1991, 7, 19)),
            ("19910719150000", "APPR", "12000000", date(1991, 7, 20)),
            (None, "APPR", "12000000", date(1991, 7, 19)),
        ]
    ):
        location = TblFundorte(
            amt=ags,
            plz=10178,
            ort="Berlin-Mitte",
            strasse="Testweg",
            kreis="Berlin",
            land="Berlin",
            beschreibung=1,
            latitude="52.52",
            longitude="13.4",
            ablage=f"1990/1990-01-01/Berlin-Mitte-{timestamp}-{index}.webp",
        )
        session.add(
            TblMeldungen(
                fundort=location,
                dat_fund_von=found,
                statuses=[status],
            )
        )
    session.commit()


@pytest.mark.parametrize(
    "ags,day,counts",
    [
        ("", "1991-07-19", {"0": 1, "1": 2, "23": 1}),
        ("12", "1991-07-19", {"0": 1, "1": 2}),
        ("99", "1991-07-19", {}),
        ("", "1991-07-18", {}),
    ],
)
def test_hourly_chart_counts_approved_reports(
    authenticated_client, hourly_reports, ags, day, counts
):
    response = authenticated_client.post(
        "/statistik",
        data={
            "stats": "meldungen_zeiten",
            "dateFrom": day,
            "dateTo": day,
            "ags": ags,
        },
    )
    assert response.status_code == 200
    chart = re.search(r"var daten = (.*);", response.text)
    assert chart is not None
    assert json.loads(chart[1]) == {
        str(hour): counts.get(str(hour), 0) for hour in range(24)
    }
