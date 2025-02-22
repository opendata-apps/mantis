from sqlalchemy import text
import app.database.full_text_search as fts

#@pytest.fixture(scope='session')
def test_view_fulltextsearch1(session):
    search_query = "Zossen"
    search_vector = text(
        "plainto_tsquery('german', :query)"
    ).bindparams(
        # Option 2: Use plainto_tsquery
        query=f"{search_query}"
    )
    search_results = session.query(fts.FullTextSearch).filter(
        fts.FullTextSearch.doc.op("@@")(search_vector)
    ).all()
    reported_sightings_ids = [
        result.meldungen_id for result in search_results
    ]

    assert  reported_sightings_ids == [1]

#@pytest.fixture(scope='session')
def test_view_fulltextsearch_with_umlaut(session):
    search_query = "Cottbus"
    search_vector = text(
        "plainto_tsquery('german', :query)"
    ).bindparams(
        # Option 2: Use plainto_tsquery
        query=f"{search_query}"
    )
    search_results = session.query(fts.FullTextSearch).filter(
        fts.FullTextSearch.doc.op("@@")(search_vector)
    ).all()
    reported_sightings_ids = [
        result.meldungen_id for result in search_results
    ]

    assert  reported_sightings_ids == [3, 9]
