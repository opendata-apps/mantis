from datetime import date, timedelta

from bs4 import BeautifulSoup
import pytest
from werkzeug.datastructures import MultiDict

from app import forms


@pytest.mark.parametrize(
    "today, earliest",
    [(date(2026, 3, 12), date(2021, 3, 12)), (date(2024, 2, 29), date(2019, 2, 28))],
)
def test_five_calendar_years_in_form_and_browser(
    client, app, monkeypatch, today, earliest
):
    class ClockDate(date):
        @classmethod
        def today(cls):
            return today

    monkeypatch.setattr(forms, "date", ClockDate)
    with app.test_request_context():
        for value, accepted in (
            (earliest, True),
            (earliest - timedelta(days=1), False),
        ):
            form = forms.MantisSightingForm(
                MultiDict({"sighting_date": value.isoformat()})
            )
            assert form.sighting_date.validate(form) is accepted

    page = BeautifulSoup(client.get("/melden").text, "html.parser")
    field = page.select_one("#sighting_date")
    assert field is not None
    assert field["min"] == earliest.isoformat()
