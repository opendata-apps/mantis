import pytest
from sqlalchemy import text
import app.database.full_text_search as fts

# Individual tests - keeping these for clarity
def test_view_fulltextsearch_zossen(session, request_context):
    """Test that the full text search finds a record with 'Zossen'."""
    search_query = "Zossen"
    search_vector = text(
        "plainto_tsquery('german', :query)"
    ).bindparams(
        query=search_query
    )
    search_results = session.query(fts.FullTextSearch).filter(
        fts.FullTextSearch.doc.op("@@")(search_vector)
    ).all()
    reported_sightings_ids = [
        result.meldungen_id for result in search_results
    ]

    assert reported_sightings_ids == [1]

def test_view_fulltextsearch_cottbus(session, request_context):
    """Test that the full text search finds records with 'Cottbus'."""
    search_query = "Cottbus"
    search_vector = text(
        "plainto_tsquery('german', :query)"
    ).bindparams(
        query=search_query
    )
    search_results = session.query(fts.FullTextSearch).filter(
        fts.FullTextSearch.doc.op("@@")(search_vector)
    ).all()
    reported_sightings_ids = [
        result.meldungen_id for result in search_results
    ]

    assert reported_sightings_ids == [3, 9]

# Parameterized test - more maintainable for adding new test cases
@pytest.mark.parametrize("search_term,expected_ids", [
    ("Zossen", [1]),
    ("Cottbus", [3, 9]),
    ("Berlin", [11, 16]),  # Test data contains Berlin entries
])
def test_full_text_search_parameterized(session, request_context, search_term, expected_ids):
    """Test full text search with different search terms using parameterization."""
    search_vector = text(
        "plainto_tsquery('german', :query)"
    ).bindparams(
        query=search_term
    )
    
    search_results = session.query(fts.FullTextSearch).filter(
        fts.FullTextSearch.doc.op("@@")(search_vector)
    ).all()
    
    reported_sightings_ids = [
        result.meldungen_id for result in search_results
    ]

    assert reported_sightings_ids == expected_ids, \
        f"Expected IDs {expected_ids} for search term '{search_term}' but got {reported_sightings_ids}"
