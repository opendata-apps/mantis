import json
import re

import pytest


@pytest.mark.parametrize(
    "ags,expected",
    [
        (
            "",
            {
                "Männchen": 3,
                "Weibchen": 2,
                "Nymphen": 3,
                "Ootheken": 4,
                "Andere": 5,
                "Gesamt": 17,
            },
        ),
        (
            "11",
            {
                "Männchen": 1,
                "Weibchen": 2,
                "Nymphen": 3,
                "Ootheken": 4,
                "Andere": 5,
                "Gesamt": 15,
            },
        ),
    ],
)
def test_gender_chart_counts_approved_reports(
    authenticated_client, counted_reports, ags, expected
):
    response = authenticated_client.post(
        "/statistik",
        data={
            "stats": "geschlecht",
            "dateFrom": "1992-06-10",
            "dateTo": "1992-06-10",
            "ags": ags,
        },
    )
    assert response.status_code == 200
    chart = re.search(r"var daten = (.*);", response.text)
    assert chart is not None
    assert json.loads(chart[1]) == expected
