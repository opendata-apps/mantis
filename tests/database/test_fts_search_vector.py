"""Tests for native PostgreSQL full-text search via search_vector column."""

from datetime import date

import pytest

from sqlalchemy import select, func
from app.database.models import TblMeldungen

SEEDED_SAMPLE_IDS = {1, 3, 9, 11, 16}


class TestSearchVector:
    """Test the search_vector column on meldungen."""

    def test_search_vector_populated(self, session):
        """Verify search_vector is populated for existing rows."""
        result = session.execute(
            select(TblMeldungen.id, TblMeldungen.search_vector).where(
                TblMeldungen.search_vector.is_not(None)
            )
        ).first()
        assert result is not None, (
            "At least one row should have a populated search_vector"
        )

    def test_search_by_city(self, session):
        """Search for a city name via the search_vector."""
        ts_query = func.websearch_to_tsquery("german", "Cottbus")
        results = session.scalars(
            select(TblMeldungen.id)
            .where(TblMeldungen.id.in_(SEEDED_SAMPLE_IDS))
            .where(TblMeldungen.search_vector.op("@@")(ts_query))
        ).all()
        assert set(results) == {3, 9}

    def test_search_by_city_case_insensitive(self, session):
        """FTS is case-insensitive by design."""
        ts_query = func.websearch_to_tsquery("german", "cottbus")
        results = session.scalars(
            select(TblMeldungen.id)
            .where(TblMeldungen.id.in_(SEEDED_SAMPLE_IDS))
            .where(TblMeldungen.search_vector.op("@@")(ts_query))
        ).all()
        assert set(results) == {3, 9}

    def test_search_berlin(self, session):
        """Search for Berlin."""
        ts_query = func.websearch_to_tsquery("german", "Berlin")
        results = session.scalars(
            select(TblMeldungen.id)
            .where(TblMeldungen.id.in_(SEEDED_SAMPLE_IDS))
            .where(TblMeldungen.search_vector.op("@@")(ts_query))
        ).all()
        assert set(results) == {11, 16}

    def test_search_zossen(self, session):
        """Search for Zossen."""
        ts_query = func.websearch_to_tsquery("german", "Zossen")
        results = session.scalars(
            select(TblMeldungen.id)
            .where(TblMeldungen.id.in_(SEEDED_SAMPLE_IDS))
            .where(TblMeldungen.search_vector.op("@@")(ts_query))
        ).all()
        assert set(results) == {1}

    def test_search_with_ranking(self, session):
        """Verify ts_rank_cd returns float scores."""
        ts_query = func.websearch_to_tsquery("german", "Berlin")
        results = session.execute(
            select(
                TblMeldungen.id,
                func.ts_rank_cd(TblMeldungen.search_vector, ts_query).label("rank"),
            )
            .where(TblMeldungen.search_vector.op("@@")(ts_query))
            .order_by(func.ts_rank_cd(TblMeldungen.search_vector, ts_query).desc())
        ).all()
        assert len(results) > 0
        assert all(r.rank > 0 for r in results)

    def test_search_no_results(self, session):
        """Search for a term that doesn't exist returns empty."""
        ts_query = func.websearch_to_tsquery("german", "Xyznonexistent")
        results = session.scalars(
            select(TblMeldungen.id).where(TblMeldungen.search_vector.op("@@")(ts_query))
        ).all()
        assert results == []

    def test_meldung_without_fundort_or_melder_is_searchable(self, session):
        """A meldung is findable even when its joined rows are missing.

        Both are optional: ``fo_zuordnung`` is nullable, and the melduser link
        is written after the meldung. The trigger used to read those rows with
        ``SELECT ... INTO``, which assigns NULL when nothing matches, and a NULL
        operand nulls the whole ``||`` chain — the report became unsearchable.
        """
        meldung = TblMeldungen(
            dat_fund_von=date(2025, 8, 1),
            fo_zuordnung=None,
            anm_melder="Gottesanbeterin Xylophonstrasse",
        )
        session.add(meldung)
        session.flush()

        ts_query = func.websearch_to_tsquery("german", "Xylophonstrasse")
        found = session.scalars(
            select(TblMeldungen.id)
            .where(TblMeldungen.id == meldung.id)
            .where(TblMeldungen.search_vector.op("@@")(ts_query))
        ).all()
        assert found == [meldung.id]

    def test_search_websearch_syntax_negation(self, session):
        """websearch_to_tsquery supports -exclude syntax."""
        ts_query = func.websearch_to_tsquery("german", "Cottbus -Berlin")
        results = session.scalars(
            select(TblMeldungen.id).where(TblMeldungen.search_vector.op("@@")(ts_query))
        ).all()
        # Should find Cottbus results but not Berlin
        assert 3 in results or 9 in results
        assert 11 not in results
        assert 16 not in results


@pytest.mark.parametrize(
    "target", ["location", "reporter", "description", "reporter_link"]
)
def test_search_tracks_related_edits(session, target):
    from app.database.models import TblUsers

    report = session.get(TblMeldungen, 1)
    query = select(TblMeldungen.id).where(
        TblMeldungen.id == report.id,
        TblMeldungen.search_vector.op("@@")(
            func.websearch_to_tsquery("german", "Zebrafalterprobe")
        ),
    )
    assert session.scalar(query) is None
    if target == "location":
        record, field = report.fundort, "ort"
    elif target == "reporter":
        record, field = report.reporter_link.reporter, "user_name"
    elif target == "description":
        record, field = report.fundort.location_type, "beschreibung"
    else:
        record = TblUsers(
            user_id="fts-replacement", user_name="Zebrafalterprobe", user_rolle="1"
        )
        session.add(record)
        session.flush()
        original_reporter = report.reporter_link.reporter
        report.reporter_link.reporter = record
        session.flush()
        assert session.scalar(query) == report.id
        report.reporter_link.reporter = original_reporter
        session.flush()
        assert session.scalar(query) is None
        return

    original = getattr(record, field)
    setattr(record, field, "Zebrafalterprobe")
    session.flush()
    assert session.scalar(query) == report.id
    setattr(record, field, original)
    session.flush()
    assert session.scalar(query) is None
