"""Tests for native PostgreSQL full-text search via search_vector column."""

import pytest
from sqlalchemy import select, func
from app.database.models import TblMeldungen

SEEDED_SAMPLE_IDS = {1, 3, 9, 11, 16}


class TestSearchVector:
    """Test the search_vector column on meldungen."""

    def test_search_vector_populated(self, session, request_context):
        """Verify search_vector is populated for existing rows."""
        result = session.execute(
            select(TblMeldungen.id, TblMeldungen.search_vector)
            .where(TblMeldungen.search_vector.is_not(None))
        ).first()
        assert result is not None, "At least one row should have a populated search_vector"

    def test_search_by_city(self, session, request_context):
        """Search for a city name via the search_vector."""
        ts_query = func.websearch_to_tsquery("german", "Cottbus")
        results = session.scalars(
            select(TblMeldungen.id)
            .where(TblMeldungen.id.in_(SEEDED_SAMPLE_IDS))
            .where(TblMeldungen.search_vector.op("@@")(ts_query))
        ).all()
        assert set(results) == {3, 9}

    def test_search_by_city_case_insensitive(self, session, request_context):
        """FTS is case-insensitive by design."""
        ts_query = func.websearch_to_tsquery("german", "cottbus")
        results = session.scalars(
            select(TblMeldungen.id)
            .where(TblMeldungen.id.in_(SEEDED_SAMPLE_IDS))
            .where(TblMeldungen.search_vector.op("@@")(ts_query))
        ).all()
        assert set(results) == {3, 9}

    def test_search_berlin(self, session, request_context):
        """Search for Berlin."""
        ts_query = func.websearch_to_tsquery("german", "Berlin")
        results = session.scalars(
            select(TblMeldungen.id)
            .where(TblMeldungen.id.in_(SEEDED_SAMPLE_IDS))
            .where(TblMeldungen.search_vector.op("@@")(ts_query))
        ).all()
        assert set(results) == {11, 16}

    def test_search_zossen(self, session, request_context):
        """Search for Zossen."""
        ts_query = func.websearch_to_tsquery("german", "Zossen")
        results = session.scalars(
            select(TblMeldungen.id)
            .where(TblMeldungen.id.in_(SEEDED_SAMPLE_IDS))
            .where(TblMeldungen.search_vector.op("@@")(ts_query))
        ).all()
        assert set(results) == {1}

    def test_search_with_ranking(self, session, request_context):
        """Verify ts_rank_cd returns float scores."""
        ts_query = func.websearch_to_tsquery("german", "Berlin")
        results = session.execute(
            select(
                TblMeldungen.id,
                func.ts_rank_cd(TblMeldungen.search_vector, ts_query).label("rank")
            )
            .where(TblMeldungen.search_vector.op("@@")(ts_query))
            .order_by(func.ts_rank_cd(TblMeldungen.search_vector, ts_query).desc())
        ).all()
        assert len(results) > 0
        assert all(r.rank > 0 for r in results)

    def test_search_no_results(self, session, request_context):
        """Search for a term that doesn't exist returns empty."""
        ts_query = func.websearch_to_tsquery("german", "Xyznonexistent")
        results = session.scalars(
            select(TblMeldungen.id)
            .where(TblMeldungen.search_vector.op("@@")(ts_query))
        ).all()
        assert results == []

    def test_search_websearch_syntax_negation(self, session, request_context):
        """websearch_to_tsquery supports -exclude syntax."""
        ts_query = func.websearch_to_tsquery("german", "Cottbus -Berlin")
        results = session.scalars(
            select(TblMeldungen.id)
            .where(TblMeldungen.search_vector.op("@@")(ts_query))
        ).all()
        # Should find Cottbus results but not Berlin
        assert 3 in results or 9 in results
        assert 11 not in results
        assert 16 not in results
