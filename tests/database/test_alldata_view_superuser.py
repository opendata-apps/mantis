"""Search results in the reviewer data table."""

import re

from sqlalchemy import select

from app.database.models import TblMeldungen


def grid_ids(response):
    return [int(id_) for id_ in re.findall(r'id="cell-(\d+)-tiere"', response.text)]


def test_view_alldata_search(authenticated_client, session):
    report = session.scalar(select(TblMeldungen).order_by(TblMeldungen.id))
    report.anm_melder = "Zebrafaltertest"
    session.commit()
    htmx = {"HX-Request": "true"}

    response = authenticated_client.get(
        "/alldata", query_string={"q": "Zebrafaltertest"}, headers=htmx
    )
    assert response.status_code == 200
    assert grid_ids(response) == [report.id]

    missing = authenticated_client.get(
        "/alldata", query_string={"q": "NoMatchingZebrafalter"}, headers=htmx
    )
    assert missing.status_code == 200
    assert grid_ids(missing) == []
