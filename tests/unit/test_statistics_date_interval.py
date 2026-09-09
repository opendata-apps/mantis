"""Only parsable dates may reach the session.

Every statistics view reads session["date_from"] back through
date.fromisoformat, so an unparsable value poisons that reviewer's session
rather than failing a single request.
"""

from datetime import date, timedelta

import pytest

from app.routes.statistics import get_date_interval

TODAY = date.today()
LAST_YEAR = (TODAY - timedelta(weeks=52)).isoformat()


def test_defaults_span_the_last_year(app):
    with app.test_request_context(method="POST", data={}):
        assert get_date_interval() == (LAST_YEAR, TODAY.isoformat())


def test_submitted_dates_are_kept(app):
    with app.test_request_context(
        method="POST", data={"dateFrom": "2026-03-01", "dateTo": "2026-04-01"}
    ):
        assert get_date_interval() == ("2026-03-01", "2026-04-01")


@pytest.mark.parametrize("bad", ["heute", "2026-13-45", "", "2026/03/01", "../etc"])
def test_unparsable_input_falls_back(app, bad):
    with app.test_request_context(method="POST", data={"dateFrom": bad}):
        date_from, _ = get_date_interval()

    assert date_from == LAST_YEAR
    date.fromisoformat(date_from)


def test_a_poisoned_session_recovers_on_the_next_request(app):
    """The failure mode: bad value already stored, every later view raising."""
    with app.test_request_context(method="GET"):
        from flask import session

        session["date_from"] = "kaputt"
        session["date_to"] = "auch kaputt"

        date_from, date_to = get_date_interval()

    assert (date_from, date_to) == (LAST_YEAR, TODAY.isoformat())


def test_datetime_input_is_truncated_to_the_date(app):
    """The form sends full ISO timestamps; only the date half is stored."""
    with app.test_request_context(
        method="POST", data={"dateFrom": "2026-03-01T14:22:05.123456"}
    ):
        assert get_date_interval()[0] == "2026-03-01"
