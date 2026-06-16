"""Tests for the public map endpoint (/auswertungen)."""

import re
from datetime import date

from sqlalchemy import func, select

from app import db
from app.database.models import (
    ReportStatus,
    TblFundorte,
    TblFundortBeschreibung,
    TblMeldungen,
)


def _approved_in_range_count(min_year):
    stmt = (
        select(func.count())
        .select_from(TblMeldungen)
        .join(TblMeldungen.fundort)
        .where(
            TblMeldungen.dat_fund_von >= date(min_year, 1, 1),
            TblMeldungen.statuses.contains([ReportStatus.APPR.value]),
        )
    )
    return db.session.scalar(stmt)


def test_map_renders_every_approved_report(client, session, app):
    """post_count must equal the number of approved in-range reports.

    Coordinates come from non-nullable Double columns with CHECK range
    constraints, so the map loop can never drop a row. This guards against a
    future change reintroducing row-dropping coordinate validation here.
    """
    min_year = app.config["MIN_MAP_YEAR"]
    beschreibung = session.scalar(select(TblFundortBeschreibung))
    assert beschreibung, "No beschreibung records found in database"

    location = TblFundorte(
        mtb="3644",
        longitude=13.404954,
        latitude=52.520008,
        ort="Map Test City",
        land="Test State",
        kreis="Test District",
        strasse="Test Street",
        plz="10178",
        amt="Test Amt",
        ablage="map_test.jpg",
        beschreibung=beschreibung.id,
    )
    session.add(location)
    session.flush()

    sighting = TblMeldungen(
        dat_fund_von=date(min_year + 1, 6, 1),
        dat_meld=date(min_year + 1, 6, 2),
        fo_zuordnung=location.id,
        statuses=[ReportStatus.APPR.value],
        art_m=1,
        art_w=0,
        art_n=0,
        art_o=0,
    )
    session.add(sighting)
    session.commit()

    expected = _approved_in_range_count(min_year)
    assert expected >= 1

    response = client.get("/auswertungen")
    assert response.status_code == 200

    html = response.get_data(as_text=True)
    match = re.search(r'data-target="(\d+)"', html)
    assert match, "post_count target not found in rendered map"
    assert int(match.group(1)) == expected
