import pytest
from bs4 import BeautifulSoup


@pytest.mark.parametrize(
    "marker,expected",
    [
        (
            "meldungen_laender",
            {
                "11 -- Berlin": [1, 2, 3, 4, 5, 15],
                "12 -- Brandenburg": [2, 0, 0, 0, 0, 2],
            },
        ),
        ("meldungen_brb", {"12062 -- Landkreis Elbe-Elster": [2, 0, 0, 0, 0, 2]}),
        ("meldungen_berlin", {"11000001 -- Mitte": [1, 2, 3, 4, 5, 15]}),
    ],
)
def test_region_tables_show_approved_counts(
    authenticated_client, counted_reports, marker, expected
):
    response = authenticated_client.post(
        "/statistik",
        data={
            "stats": marker,
            "dateFrom": "1992-06-10",
            "dateTo": "1992-06-10",
        },
    )
    assert response.status_code == 200
    soup = BeautifulSoup(response.data, "html.parser")
    tables = {}
    for table in soup.select("table"):
        heading = table.find_previous("h1")
        assert heading is not None
        label = " ".join(heading.get_text().split())
        tables[label] = [
            int(row.select("td")[1].text) for row in table.select("tbody tr")
        ]
    assert tables == expected
