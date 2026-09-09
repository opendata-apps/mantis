"""Search results and pagination counts in the reviewer data table."""

from sqlalchemy import select

from app.database.models import TblMeldungen


def test_view_alldata_search(authenticated_client, session):
    report = session.scalar(select(TblMeldungen).order_by(TblMeldungen.id))
    report.anm_melder = "Zebrafaltertest"
    session.commit()

    response = authenticated_client.get(
        "/admin/get_table_data/all_data_view",
        query_string={"search": "Zebrafaltertest", "per_page": 1},
    )
    assert response.status_code == 200
    result = response.json
    id_column = result["columns"].index("meldungen_id")
    assert result["total_items"] == 1
    assert [row[id_column] for row in result["data"]] == [report.id]

    missing = authenticated_client.get(
        "/admin/get_table_data/all_data_view",
        query_string={"search": "NoMatchingZebrafalter"},
    )
    assert missing.status_code == 200
    assert missing.json["total_items"] == 0
    assert missing.json["data"] == []
