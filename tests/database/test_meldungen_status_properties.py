"""Tests for TblMeldungen boolean status properties.

These verify the convenience properties (is_deleted, is_approved,
is_open, is_unclear, needs_info) that the admin UI and query filters rely on.
"""

import pytest
from datetime import date
from sqlalchemy import select
from app.database.models import STATUS_FILTERS, TblMeldungen, ReportStatus


@pytest.fixture
def make_sighting(session):
    """Factory that creates a TblMeldungen with given statuses."""
    existing = session.scalar(select(TblMeldungen).order_by(TblMeldungen.id))
    if not existing:
        pytest.skip("No existing sightings in test database")

    def _make(statuses):
        sighting = TblMeldungen(
            dat_fund_von=date.today(),
            dat_meld=date.today(),
            fo_zuordnung=existing.fo_zuordnung,
            statuses=statuses,
            deleted=ReportStatus.DEL.value in statuses,
        )
        session.add(sighting)
        session.flush()
        return sighting

    return _make


# ---------------------------------------------------------------------------
# Boolean properties — each tests True and False
# ---------------------------------------------------------------------------
class TestIsDeleted:
    def test_true_when_del_present(self, make_sighting):
        s = make_sighting(["DEL"])
        assert s.is_deleted is True

    def test_false_when_open(self, make_sighting):
        s = make_sighting(["OPEN"])
        assert s.is_deleted is False

    def test_false_when_approved(self, make_sighting):
        s = make_sighting(["APPR"])
        assert s.is_deleted is False


class TestIsApproved:
    def test_true_when_appr_present(self, make_sighting):
        s = make_sighting(["APPR"])
        assert s.is_approved is True

    def test_false_when_open(self, make_sighting):
        s = make_sighting(["OPEN"])
        assert s.is_approved is False


class TestIsOpen:
    def test_true_when_open_present(self, make_sighting):
        s = make_sighting(["OPEN"])
        assert s.is_open is True

    def test_true_with_flags(self, make_sighting):
        s = make_sighting(["OPEN", "INFO"])
        assert s.is_open is True

    def test_false_when_approved(self, make_sighting):
        s = make_sighting(["APPR"])
        assert s.is_open is False


class TestIsUnclear:
    def test_true_when_unkl_present(self, make_sighting):
        s = make_sighting(["OPEN", "UNKL"])
        assert s.is_unclear is True

    def test_false_when_no_unkl(self, make_sighting):
        s = make_sighting(["OPEN"])
        assert s.is_unclear is False

    def test_false_when_approved(self, make_sighting):
        s = make_sighting(["APPR"])
        assert s.is_unclear is False


class TestNeedsInfo:
    def test_true_when_info_present(self, make_sighting):
        s = make_sighting(["OPEN", "INFO"])
        assert s.needs_info is True

    def test_false_when_no_info(self, make_sighting):
        s = make_sighting(["OPEN"])
        assert s.needs_info is False

    def test_false_when_deleted(self, make_sighting):
        s = make_sighting(["DEL"])
        assert s.needs_info is False


# ---------------------------------------------------------------------------
# Property combinations — realistic workflow states
# ---------------------------------------------------------------------------
class TestPropertyCombinations:
    """Verify properties are consistent for real-world status combos."""

    def test_open_with_both_flags(self, make_sighting):
        s = make_sighting(["OPEN", "INFO", "UNKL"])
        assert s.is_open is True
        assert s.needs_info is True
        assert s.is_unclear is True
        assert s.is_approved is False
        assert s.is_deleted is False

    def test_approved_has_no_flags(self, make_sighting):
        s = make_sighting(["APPR"])
        assert s.is_approved is True
        assert s.is_open is False
        assert s.is_deleted is False
        assert s.is_unclear is False
        assert s.needs_info is False

    def test_deleted_has_no_flags(self, make_sighting):
        s = make_sighting(["DEL"])
        assert s.is_deleted is True
        assert s.is_open is False
        assert s.is_approved is False
        assert s.is_unclear is False
        assert s.needs_info is False

    def test_none_statuses_all_false(self, make_sighting):
        s = make_sighting(["OPEN"])
        s.statuses = None
        assert s.is_open is False
        assert s.is_approved is False
        assert s.is_deleted is False
        assert s.is_unclear is False
        assert s.needs_info is False


class TestHybridSqlMatchesPython:
    """A hybrid is only useful if both halves agree.

    These properties are used two ways: as a WHERE clause when the reviewer
    list is queried, and as a plain attribute when a single card is
    re-rendered over HTMX. If the SQL and the Python drifted apart, a report
    would show up in the list and then vanish on its next refresh.
    """

    @pytest.fixture(autouse=True)
    def _rows(self, make_sighting):
        # One report per status combination the workflow allows.
        for statuses in (
            ["OPEN"],
            ["OPEN", "INFO"],
            ["OPEN", "UNKL"],
            ["OPEN", "INFO", "UNKL"],
            ["APPR"],
            ["DEL"],
        ):
            make_sighting(statuses)

    @pytest.mark.parametrize("filter_name,attribute", sorted(STATUS_FILTERS.items()))
    def test_sql_selects_exactly_the_python_matches(
        self, session, filter_name, attribute
    ):
        selected = set(
            session.scalars(
                select(TblMeldungen.id).where(getattr(TblMeldungen, attribute))
            )
        )
        expected = {
            row.id
            for row in session.scalars(select(TblMeldungen))
            if getattr(row, attribute)
        }
        assert selected == expected, f"{filter_name} disagrees between SQL and Python"

    def test_pending_excludes_flagged_reports(self, session):
        """ "offen" must mean OPEN without INFO or UNKL, in both halves."""
        pending = session.scalars(
            select(TblMeldungen).where(TblMeldungen.is_pending)
        ).all()

        assert pending, "expected at least one pending report"
        for row in pending:
            assert row.is_open and not row.needs_info and not row.is_unclear
