"""Test that status-based filtering works correctly."""

from datetime import datetime

import pytest
from sqlalchemy import select

from app.database.models import ReportStatus, TblMeldungen
from app.routes.admin.filters import get_filtered_query, normalize_filter_status
from app.routes.admin.reviewer import _matches_filter_status


class TestIsComparisonFilters:
    """Direct unit tests for the filter query logic with status-based filtering."""

    def test_unspecified_gender_filter(self, session):
        """Test the nicht_bestimmt filter for unspecified gender."""
        stmt = get_filtered_query(filter_type="nicht_bestimmt")
        results = session.execute(stmt).all()

        for row in results:
            meldung = row[0]
            # All gender fields should be None or 0
            assert not meldung.art_m, f"Sighting {meldung.id} has art_m={meldung.art_m}"
            assert not meldung.art_w, f"Sighting {meldung.id} has art_w={meldung.art_w}"
            assert not meldung.art_n, f"Sighting {meldung.id} has art_n={meldung.art_n}"
            assert not meldung.art_o, f"Sighting {meldung.id} has art_o={meldung.art_o}"
            assert not meldung.art_f, f"Sighting {meldung.id} has art_f={meldung.art_f}"

    @pytest.mark.parametrize(
        "counts", [(0, 0, 0, 0, 0), (None,) * 5, (None, 0, None, 0, 0)]
    )
    def test_unspecified_filter_includes_saved_unclassified_report(
        self, session, counts
    ):
        report = session.scalar(select(TblMeldungen).order_by(TblMeldungen.id))
        assert report is not None
        report.art_m, report.art_w, report.art_n, report.art_o, report.art_f = counts
        session.flush()

        reports = session.scalars(
            get_filtered_query(filter_status="all", filter_type="nicht_bestimmt")
        ).all()
        assert report in reports

    def test_combined_status_and_type_filters(self, session):
        """Test combining status and type filters."""
        # Test open + male
        stmt = get_filtered_query(filter_status="offen", filter_type="maennlich")
        results = session.execute(stmt).all()

        for row in results:
            meldung = row[0]
            assert meldung.is_open, "Non-OPEN status in open filter"
            assert meldung.art_m >= 1, "Non-male sighting in male filter"

    def test_default_filter_behavior(self, session):
        """Test default behavior when no filter specified."""
        # Default should exclude deleted items
        stmt = get_filtered_query()
        results = session.execute(stmt).all()

        for row in results:
            meldung = row[0]
            assert not meldung.is_deleted, (
                f"Deleted sighting {meldung.id} shown in default view"
            )

    def test_status_field_edge_cases(self, session):
        """Test edge cases with all status values."""
        from app.database.models import TblMeldungUser

        # Get any existing sighting with full relationships to use as template
        # ORDER BY id to ensure deterministic selection
        existing = session.scalar(select(TblMeldungen).order_by(TblMeldungen.id))
        if not existing:
            pytest.skip("No existing sightings in test database")
        existing_rel = session.scalar(
            select(TblMeldungUser).where(TblMeldungUser.id_meldung == existing.id)
        )

        # Create test sightings with different status values
        # Flags (INFO/UNKL) only exist combined with OPEN — enforced by
        # the ck_meldungen_statuses_valid CHECK constraint.
        test_cases = [
            ([ReportStatus.OPEN.value], "status_open"),
            ([ReportStatus.APPR.value], "status_approved"),
            ([ReportStatus.DEL.value], "status_deleted"),
            ([ReportStatus.OPEN.value, ReportStatus.INFO.value], "status_info"),
            ([ReportStatus.OPEN.value, ReportStatus.UNKL.value], "status_unclear"),
        ]

        created_sightings = {}
        for status_vals, name in test_cases:
            sighting = TblMeldungen(
                dat_fund_von=datetime(2020, 1, 1).date(),
                dat_meld=datetime.now().date(),
                fo_zuordnung=existing.fo_zuordnung,
                statuses=status_vals,
                anm_melder=name,
            )
            session.add(sighting)
            session.flush()
            created_sightings[name] = sighting.id

            # Create user relationship
            if existing_rel:
                rel = TblMeldungUser(
                    id_meldung=sighting.id, id_user=existing_rel.id_user
                )
                session.add(rel)

        session.commit()

        # Test each filter
        filters_expected = {
            "offen": ["status_open"],
            "bearbeitet": ["status_approved"],
            "geloescht": ["status_deleted"],
            "informiert": ["status_info"],
            "unklar": ["status_unclear"],
            "all": [
                "status_open",
                "status_approved",
                "status_deleted",
                "status_info",
                "status_unclear",
            ],
        }

        for filter_status, expected_names in filters_expected.items():
            stmt = get_filtered_query(filter_status=filter_status)
            results = session.execute(stmt).all()

            result_ids = [row[0].id for row in results]

            assert set(result_ids) & set(created_sightings.values()) == {
                created_sightings[name] for name in expected_names
            }


class TestFilterStatusNormalisation:
    """The list query and the per-card check must read a filter value alike.

    They are reached by different routes — one takes ``statusInput`` off the
    URL, the other ``filter_status`` out of an HTMX form body — so both go
    through ``normalize_filter_status``. Before that, a value like "Offen"
    filtered the list one way and decided card visibility another, and a
    report would vanish from the list on its next refresh.
    """

    @pytest.mark.parametrize("given", ["Offen", "OFFEN", " offen "])
    def test_query_ignores_casing_and_padding(self, given):
        assert normalize_filter_status(given) == "offen"

    @pytest.mark.parametrize("given", ["Geloescht", "GELOESCHT", " geloescht "])
    def test_card_visibility_ignores_casing_and_padding(self, given):
        """A deleted report tells the two paths apart.

        An unrecognised filter value falls back to "show everything not
        deleted", which happens to be the right answer for an open report —
        so only a deleted one actually detects the mismatch.
        """
        deleted = TblMeldungen(statuses=["DEL"])

        assert _matches_filter_status(deleted, given) is True
        assert _matches_filter_status(deleted, "Offen") is False

    def test_blank_value_falls_back_to_the_default(self):
        assert normalize_filter_status(None) == "offen"
        assert normalize_filter_status("") == "offen"
