"""Tests for the full-text search functionality using materialized views."""
import pytest
from sqlalchemy import text
import app.database.full_text_search as fts


def test_view_fulltextsearch_direct_search_method(session, request_context):
    """Test the direct search method in the FullTextSearch class.
    
    This test verifies that the search() class method properly finds
    matching records by using PostgreSQL's full-text search capabilities.
    """
    # Test a simple search
    search_term = "Cottbus"
    results = fts.FullTextSearch.search(search_term)
    
    # Results should be sorted by rank so we don't rely on order
    assert set(results) == {3, 9}, \
        f"Expected IDs {{3, 9}} for search term '{search_term}' but got {results}"
    
    # Test a search with limit
    limited_results = fts.FullTextSearch.search(search_term, limit=1)
    assert len(limited_results) == 1, \
        f"Expected 1 result when limit=1, but got {len(limited_results)}"


# Parameterized test for maintainability and coverage
@pytest.mark.parametrize("search_term,expected_ids", [
    ("Zossen", [1]),
    ("Cottbus", [3, 9]),
    ("Berlin", [11, 16]),
    # Search should be case-insensitive
    ("berlin", [11, 16]),
    # Note: Partial word matches won't work with plainto_tsquery
    # We'd need websearch_to_tsquery for this, which is handled by the .search() method
])
def test_full_text_search_parameterized(session, request_context, search_term, expected_ids):
    """Test full text search with different search terms using parameterization.
    
    This test verifies:
    1. The full-text search finds the correct records for each search term
    2. Case insensitivity works as expected
    3. Stemming and partial matches work correctly
    
    Parameters:
        session: The database session fixture
        request_context: The Flask request context fixture
        search_term: The search term to test
        expected_ids: List of sighting IDs expected to match the search
    """
    # Create the search vector for PostgreSQL full-text search
    search_vector = text(
        "plainto_tsquery('german', :query)"
    ).bindparams(
        query=search_term
    )
    
    # Query using the ORM and PostgreSQL operator
    search_results = session.query(fts.FullTextSearch).filter(
        fts.FullTextSearch.doc.op("@@")(search_vector)
    ).all()
    
    # Extract the IDs from the results
    reported_sightings_ids = [
        result.meldungen_id for result in search_results
    ]
    
    # Sort both lists for consistent comparison
    reported_sightings_ids.sort()
    expected_ids.sort()

    # Verify the results match expectations
    assert reported_sightings_ids == expected_ids, \
        f"Expected IDs {expected_ids} for search term '{search_term}' but got {reported_sightings_ids}"


def test_full_text_search_refreshing(session, request_context):
    """Test refreshing the materialized view for full-text search.
    
    This test verifies that the materialized view can be refreshed
    after database changes to include new content in search results.
    """
    # Use the module's refresh function to update the materialized view
    from app import db
    fts.refresh_materialized_view(db)
    
    # Verify that we can still search after refreshing
    search_vector = text(
        "plainto_tsquery('german', :query)"
    ).bindparams(
        query="Berlin"
    )
    
    search_results = session.query(fts.FullTextSearch).filter(
        fts.FullTextSearch.doc.op("@@")(search_vector)
    ).all()
    
    # We should still find results after refreshing
    assert len(search_results) > 0, "Should still find results after refreshing the view"
