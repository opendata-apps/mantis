"""Test that status-based filtering works correctly."""

import pytest
from datetime import datetime
from app.database.models import TblMeldungen, ReportStatus
from app.routes.admin import get_filtered_query


class TestIsComparisonFilters:
    """Direct unit tests for the filter query logic with status-based filtering."""

    def test_open_filter_query(self, session):
        """Test the open filter shows only OPEN status items."""
        query = get_filtered_query(filter_status="offen")
        results = query.all()

        for row in results:
            meldung = row[0]  # First element is TblMeldungen
            assert meldung.status == ReportStatus.OPEN.value, (
                f"Sighting {meldung.id} has status={meldung.status}, expected OPEN"
            )

    def test_approved_filter_query(self, session):
        """Test the approved filter only shows APPR status items."""
        query = get_filtered_query(filter_status="bearbeitet")
        results = query.all()

        for row in results:
            meldung = row[0]
            assert meldung.status == ReportStatus.APPR.value, (
                f"Sighting {meldung.id} has status={meldung.status}, expected APPR"
            )

    def test_deleted_filter_query(self, session):
        """Test the deleted filter only shows DEL status items."""
        query = get_filtered_query(filter_status="geloescht")
        results = query.all()

        for row in results:
            meldung = row[0]
            assert meldung.status == ReportStatus.DEL.value, (
                f"Sighting {meldung.id} has status={meldung.status}, expected DEL"
            )

    def test_all_filter_query(self, session):
        """Test the all filter shows everything."""
        query = get_filtered_query(filter_status="all")
        all_results = query.all()

        # Get counts of each type
        open_query = get_filtered_query(filter_status="offen")
        approved_query = get_filtered_query(filter_status="bearbeitet")
        deleted_query = get_filtered_query(filter_status="geloescht")

        open_count = open_query.count()
        approved_count = approved_query.count()
        deleted_count = deleted_query.count()
        all_count = len(all_results)

        # All count should be >= sum of individual filters (some might overlap)
        assert all_count >= open_count, (
            "All filter shows fewer results than open filter"
        )
        assert all_count >= approved_count, (
            "All filter shows fewer results than approved filter"
        )
        assert all_count >= deleted_count, (
            "All filter shows fewer results than deleted filter"
        )

    def test_open_status_handled_correctly(self, session):
        """Test that OPEN status sightings appear in open filter."""
        from app.database.models import TblMeldungUser

        # Get any existing sighting with full relationships
        existing = session.query(TblMeldungen).first()
        if not existing:
            pytest.skip("No existing sightings in test database")

        # Create a sighting with OPEN status
        open_sighting = TblMeldungen(
            dat_fund_von=datetime.now().date(),
            dat_meld=datetime.now().date(),
            fo_zuordnung=existing.fo_zuordnung,
            status=ReportStatus.OPEN.value,
            deleted=None,
            art_m=1,
        )
        session.add(open_sighting)
        session.flush()

        # Create the user relationship (required for the join)
        existing_rel = (
            session.query(TblMeldungUser).filter_by(id_meldung=existing.id).first()
        )

        if existing_rel:
            new_rel = TblMeldungUser(
                id_meldung=open_sighting.id, id_user=existing_rel.id_user
            )
            session.add(new_rel)

        session.commit()

        # Check it appears in open filter
        open_query = get_filtered_query(filter_status="offen")
        open_ids = [row[0].id for row in open_query.all()]
        assert open_sighting.id in open_ids, (
            f"OPEN status sighting (id={open_sighting.id}) not shown in open filter"
        )

        # Check it doesn't appear in deleted filter
        deleted_query = get_filtered_query(filter_status="geloescht")
        deleted_ids = [row[0].id for row in deleted_query.all()]
        assert open_sighting.id not in deleted_ids, (
            "OPEN status sighting shown in deleted filter"
        )

    def test_unspecified_gender_filter(self, session):
        """Test the nicht_bestimmt filter for unspecified gender."""
        query = get_filtered_query(filter_type="nicht_bestimmt")
        results = query.all()

        for row in results:
            meldung = row[0]
            # All gender fields should be None or 0
            assert not meldung.art_m, f"Sighting {meldung.id} has art_m={meldung.art_m}"
            assert not meldung.art_w, f"Sighting {meldung.id} has art_w={meldung.art_w}"
            assert not meldung.art_n, f"Sighting {meldung.id} has art_n={meldung.art_n}"
            assert not meldung.art_o, f"Sighting {meldung.id} has art_o={meldung.art_o}"
            assert not meldung.art_f, f"Sighting {meldung.id} has art_f={meldung.art_f}"

    def test_combined_status_and_type_filters(self, session):
        """Test combining status and type filters."""
        # Test open + male
        query = get_filtered_query(filter_status="offen", filter_type="maennlich")
        results = query.all()

        for row in results:
            meldung = row[0]
            assert meldung.status == ReportStatus.OPEN.value, "Non-OPEN status in open filter"
            assert meldung.art_m >= 1, "Non-male sighting in male filter"

    def test_default_filter_behavior(self, session):
        """Test default behavior when no filter specified."""
        # Default should exclude deleted items
        query = get_filtered_query()
        results = query.all()

        for row in results:
            meldung = row[0]
            assert meldung.status != ReportStatus.DEL.value, (
                f"Deleted sighting {meldung.id} shown in default view"
            )

    def test_status_field_edge_cases(self, session):
        """Test edge cases with all status values."""
        from app.database.models import TblMeldungUser

        # Get any existing sighting with full relationships to use as template
        existing = session.query(TblMeldungen).first()
        if not existing:
            pytest.skip("No existing sightings in test database")
        existing_rel = (
            session.query(TblMeldungUser).filter_by(id_meldung=existing.id).first()
        )

        # Create test sightings with different status values
        test_cases = [
            (ReportStatus.OPEN.value, "status_open"),
            (ReportStatus.APPR.value, "status_approved"),
            (ReportStatus.DEL.value, "status_deleted"),
            (ReportStatus.INFO.value, "status_info"),
            (ReportStatus.UNKL.value, "status_unclear"),
        ]

        created_sightings = {}
        for status_val, name in test_cases:
            sighting = TblMeldungen(
                dat_fund_von=datetime.now().date(),
                dat_meld=datetime.now().date(),
                fo_zuordnung=existing.fo_zuordnung,
                status=status_val,
                deleted=(status_val == ReportStatus.DEL.value),
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
            "all": ["status_open", "status_approved", "status_deleted", "status_info", "status_unclear"],
        }

        for filter_status, expected_names in filters_expected.items():
            query = get_filtered_query(filter_status=filter_status)
            results = query.all()

            result_ids = [row[0].id for row in results]

            for name, sighting_id in created_sightings.items():
                if name in expected_names:
                    assert sighting_id in result_ids, (
                        f"{name} sighting not in {filter_status} filter"
                    )
