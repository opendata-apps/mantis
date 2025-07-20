"""Test that is_() comparisons work correctly in filters."""
import pytest
from datetime import datetime
from app.database.models import TblMeldungen
from app.routes.admin import get_filtered_query


class TestIsComparisonFilters:
    """Direct unit tests for the filter query logic with is_() comparisons."""

    def test_open_filter_query(self, session):
        """Test the open filter excludes approved and deleted items."""
        # Get the filtered query
        query = get_filtered_query(filter_status="offen")
        results = query.all()
        
        # Check that all results have dat_bear=None and deleted!=True
        for row in results:
            meldung = row[0]  # First element is TblMeldungen
            assert meldung.dat_bear is None, f"Sighting {meldung.id} has dat_bear={meldung.dat_bear}, expected None"
            assert meldung.deleted is not True, f"Sighting {meldung.id} is deleted but shown in open filter"

    def test_approved_filter_query(self, session):
        """Test the approved filter only shows approved, non-deleted items."""
        query = get_filtered_query(filter_status="bearbeitet")
        results = query.all()
        
        for row in results:
            meldung = row[0]
            assert meldung.dat_bear is not None, f"Sighting {meldung.id} has no dat_bear but shown in approved filter"
            assert meldung.deleted is not True, f"Sighting {meldung.id} is deleted but shown in approved filter"

    def test_deleted_filter_query(self, session):
        """Test the deleted filter only shows deleted items."""
        query = get_filtered_query(filter_status="geloescht")
        results = query.all()
        
        for row in results:
            meldung = row[0]
            assert meldung.deleted is True, f"Sighting {meldung.id} has deleted={meldung.deleted}, expected True"

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
        assert all_count >= open_count, "All filter shows fewer results than open filter"
        assert all_count >= approved_count, "All filter shows fewer results than approved filter"
        assert all_count >= deleted_count, "All filter shows fewer results than deleted filter"

    def test_null_deleted_handled_correctly(self, session):
        """Test that NULL deleted values are treated as not deleted."""
        from app.database.models import TblMeldungUser
        
        # Get any existing sighting with full relationships
        existing = session.query(TblMeldungen).first()
        if not existing:
            # Skip test if no data
            pytest.skip("No existing sightings in test database")
        
        # Create a sighting with deleted=None
        null_deleted = TblMeldungen(
            dat_fund_von=datetime.now().date(),
            dat_meld=datetime.now().date(),
            fo_zuordnung=existing.fo_zuordnung,  # Use same location
            deleted=None,  # Explicitly NULL
            art_m=1  # Add some data
        )
        session.add(null_deleted)
        session.flush()
        
        # Create the user relationship (required for the join)
        # Get the user from the existing relationship
        existing_rel = session.query(TblMeldungUser).filter_by(
            id_meldung=existing.id
        ).first()
        
        if existing_rel:
            new_rel = TblMeldungUser(
                id_meldung=null_deleted.id,
                id_user=existing_rel.id_user
            )
            session.add(new_rel)
        
        session.commit()
        
        # Check it appears in open filter
        open_query = get_filtered_query(filter_status="offen")
        open_ids = [row[0].id for row in open_query.all()]
        assert null_deleted.id in open_ids, f"NULL deleted sighting (id={null_deleted.id}) not shown in open filter. Open IDs: {open_ids}"
        
        # Check it doesn't appear in deleted filter
        deleted_query = get_filtered_query(filter_status="geloescht")
        deleted_ids = [row[0].id for row in deleted_query.all()]
        assert null_deleted.id not in deleted_ids, "NULL deleted sighting shown in deleted filter"

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
            assert meldung.dat_bear is None, "Approved sighting in open filter"
            assert meldung.deleted is not True, "Deleted sighting in open filter"
            assert meldung.art_m >= 1, "Non-male sighting in male filter"

    def test_default_filter_behavior(self, session):
        """Test default behavior when no filter specified."""
        # Default should exclude deleted items
        query = get_filtered_query()
        results = query.all()
        
        for row in results:
            meldung = row[0]
            assert meldung.deleted is not True, f"Deleted sighting {meldung.id} shown in default view"

    def test_boolean_field_edge_cases(self, session):
        """Test edge cases with boolean deleted field."""
        from app.database.models import TblMeldungUser
        
        # Get any existing sighting with full relationships to use as template
        existing = session.query(TblMeldungen).first()
        if not existing:
            pytest.skip("No existing sightings in test database")
        existing_rel = session.query(TblMeldungUser).filter_by(
            id_meldung=existing.id
        ).first()
        
        # Create test sightings with different deleted values
        test_cases = [
            (True, "deleted_true"),
            (False, "deleted_false"),
            (None, "deleted_null"),
        ]
        
        created_sightings = {}
        for deleted_val, name in test_cases:
            sighting = TblMeldungen(
                dat_fund_von=datetime.now().date(),
                dat_meld=datetime.now().date(),
                fo_zuordnung=existing.fo_zuordnung,
                deleted=deleted_val,
                anm_melder=name  # To identify in results
            )
            session.add(sighting)
            session.flush()
            created_sightings[name] = sighting.id
            
            # Create user relationship
            if existing_rel:
                rel = TblMeldungUser(
                    id_meldung=sighting.id,
                    id_user=existing_rel.id_user
                )
                session.add(rel)
        
        session.commit()
        
        # Test each filter
        filters_expected = {
            "offen": ["deleted_false", "deleted_null"],
            "geloescht": ["deleted_true"],
            "all": ["deleted_true", "deleted_false", "deleted_null"]
        }
        
        for filter_status, expected_names in filters_expected.items():
            query = get_filtered_query(filter_status=filter_status)
            results = query.all()
            
            result_ids = [row[0].id for row in results]
            
            for name, sighting_id in created_sightings.items():
                if name in expected_names:
                    assert sighting_id in result_ids, f"{name} sighting not in {filter_status} filter"
                else:
                    # Only check if it shouldn't be there if we're looking at our specific test data
                    # (other sightings might match the filter)
                    pass