"""What the reviewer search finds, for the things reviewers type.

get_filtered_query() is what the reviewer list and the Excel export both call,
so these run the search_vector, the GIN index and the query builder together.
They assert on the reports that come back rather than on the tsquery that was
built, so that changing how the query is assembled does not break them.

Report ids refer to the demo data in app/demodata/filldb.py.
"""

from datetime import date

import pytest
from bs4 import BeautifulSoup

from app.database.models import TblFundorte, TblMeldungen, TblMeldungUser, TblUsers
from app.routes.admin.filters import get_filtered_query


def _search(session, term):
    """Report ids the reviewer search returns for *term*."""
    stmt = get_filtered_query(
        filter_status="all", search_query=term, search_type="full_text"
    )
    return {meldung.id for meldung in session.scalars(stmt).unique()}


@pytest.fixture
def search_reports(session):
    reporter = TblUsers(user_id="search-regression", user_name="Probe", user_rolle="1")
    session.add(reporter)
    session.flush()
    reports = {}
    for place, note in [
        ("Jüterbog", "Die Straße"),
        ("Jueterbog", ""),
        ("Langerwisch", ""),
    ]:
        location = TblFundorte(
            ort=place,
            strasse="",
            kreis="",
            land="Brandenburg",
            beschreibung=1,
            latitude=52.3,
            longitude=13.1,
            ablage="",
        )
        session.add(location)
        session.flush()
        report = TblMeldungen(
            dat_fund_von=date(2026, 9, 1),
            dat_meld=date(2026, 9, 1),
            fo_zuordnung=location.id,
            anm_melder=note,
        )
        session.add(report)
        session.flush()
        session.add(TblMeldungUser(id_meldung=report.id, id_user=reporter.id))
        reports[place] = report.id
    session.flush()
    return reports


def test_search_link_keeps_its_query_when_default_filters_are_added(
    authenticated_client, session, search_reports
):
    session.commit()

    response = authenticated_client.get(
        "/reviewer?q=Jueter&search_type=full_text", follow_redirects=True
    )

    assert response.status_code == 200
    page = BeautifulSoup(response.data, "html.parser")
    search_input = page.find("input", attrs={"name": "q"})
    assert search_input is not None
    assert search_input.get("value") == "Jueter"
    visible_ids = {
        int(str(card["id"]).removeprefix("report-card-"))
        for card in page.select(".report-card")
    }
    assert visible_ids & set(search_reports.values()) == {
        search_reports["Jüterbog"],
        search_reports["Jueterbog"],
    }


@pytest.mark.parametrize(
    "term", ["Jüterbog", "Jueterbog", "JÜTER", "Jueter", "Ju\u0308terbog"]
)
def test_umlaut_spellings_and_prefixes_find_both_stored_spellings(
    session, search_reports, term
):
    assert _search(session, term) & set(search_reports.values()) == {
        search_reports["Jüterbog"],
        search_reports["Jueterbog"],
    }


def test_place_prefix_is_not_lost_to_german_stemming(session, search_reports):
    assert _search(session, "Langerwis") & set(search_reports.values()) == {
        search_reports["Langerwisch"],
    }


@pytest.mark.parametrize("term", ["Die", "Straße", "Strasse"])
def test_literal_words_and_sharp_s_are_searchable(session, search_reports, term):
    assert _search(session, term) & set(search_reports.values()) == {
        search_reports["Jüterbog"],
    }


class TestWhatTheSearchFinds:
    def test_a_place_name_finds_the_report_from_that_place(self, session):
        assert 8 in _search(session, "Luckenwalde")  # fundort 8 is in Luckenwalde

    def test_a_partial_place_name_finds_the_same_reports(self, session):
        """Reviewers do not type whole words; "Luckenw" used to find nothing."""
        assert _search(session, "Luckenw") == _search(session, "Luckenwalde")
        assert 8 in _search(session, "Luckenw")

    def test_umlaut_spellings_find_the_same_reports(self, session):
        """A reviewer may type Jueterbog or Jüterbog for the same place."""
        assert _search(session, "Jueterbog") == _search(session, "Jüterbog")
        assert 18 in _search(session, "Jueterbog")

    def test_a_word_from_the_reporter_note_finds_the_report(self, session):
        assert 5 in _search(session, "Unklar")  # report 5: "Unklar - bitte prüfen!"

    def test_a_contact_domain_finds_that_reporters_reports(self, session):
        """The address is indexed whole and split, so the domain is searchable."""
        assert 2 in _search(
            session, "example.com"
        )  # report 2 -> herrmann29@example.com

    def test_a_whole_contact_address_still_finds_the_report(self, session):
        assert 2 in _search(session, "herrmann29@example.com")


class TestHowTermsCombine:
    def test_adding_a_term_can_only_narrow_the_result(self, session):
        assert _search(session, "Luckenw").issuperset(
            _search(session, "Luckenw Luckenwalde")
        )
        assert _search(session, "Luckenw Cottbus") == set()  # no report is in both

    def test_two_words_need_not_be_adjacent(self, session):
        """Both words must appear, anywhere -- not as a phrase."""
        assert 2 in _search(session, "Ziesar Wiesenweg")  # ort and strasse of fundort 2

    def test_a_pipe_does_not_turn_the_search_into_an_or(self, session):
        """Typing search syntax must not widen the result set."""
        assert _search(session, "Luckenw | Cottbus") == set()


class TestSearchesThatFindNothing:
    @pytest.mark.parametrize("term", ["'", "   ", "?", "Nichtvorhandenerortsname"])
    def test_input_with_nothing_to_match_returns_no_reports(self, session, term):
        assert _search(session, term) == set()

    @pytest.mark.parametrize(
        "term", ["!!!", "* & |", "a & b", "rm -rf", "d'accord", "':*", "\\"]
    )
    def test_punctuation_does_not_break_the_search(self, session, term):
        """Whatever a reviewer types, the page must still render a result."""
        assert isinstance(_search(session, term), set)
