from typing import Optional, List, Tuple
from sqlalchemy import event, DDL, Index, text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.sql import func, expression
from flask import current_app
from app import db
from app.database.models import TblMeldungen, TblFundorte, TblFundortBeschreibung, TblMeldungUser, TblUsers

class FullTextSearch(db.Model):
    """
    A materialized view for full-text search functionality.
    Uses PostgreSQL's tsvector and websearch_to_tsquery for efficient text search operations.
    
    The search supports the following websearch syntax:
    - quoted strings for exact phrase matches: "exact phrase"
    - OR operator: word1 OR word2
    - negation: -word
    - grouping with parentheses: (word1 OR word2) word3
    """
    __tablename__ = "full_text_search"
    
    meldungen_id = db.Column(db.Integer, primary_key=True)
    doc = db.Column(TSVECTOR)
    
    # Create GIN index for faster full-text search
    __table_args__ = (
        Index('idx_fts_doc_gin', doc, postgresql_using='gin'),
        Index('idx_fts_meldungen_id', meldungen_id, unique=True),
    )
    
    @classmethod
    def search(cls, query: str, limit: Optional[int] = None) -> List[int]:
        """
        Perform a full-text search using websearch_to_tsquery.
        
        Args:
            query: The search query string using websearch syntax
            limit: Optional limit for the number of results
            
        Returns:
            List of meldungen_id that match the search criteria
            
        Example:
            >>> FullTextSearch.search('"exact phrase" -exclude')
            >>> FullTextSearch.search('word1 OR word2')
        """
        try:
            # Use websearch_to_tsquery for better search syntax support
            ts_query = expression.func.websearch_to_tsquery('german', query)
            
            # Build the search query
            search_query = cls.query.with_entities(cls.meldungen_id).\
                filter(cls.doc.op('@@')(ts_query))
                
            if limit:
                search_query = search_query.limit(limit)
                
            return [result.meldungen_id for result in search_query.all()]
        except Exception as e:
            # Log the error but don't expose internal details
            current_app.logger.error(f"FTS search error: {str(e)}")
            return []
    
    @classmethod
    def create_materialized_view(cls):
        """Create the materialized view for full-text search with optimized tsvector concatenation."""
        view_query = """
            CREATE MATERIALIZED VIEW IF NOT EXISTS full_text_search AS
            SELECT 
                m.id as meldungen_id,
                setweight(to_tsvector('german', COALESCE(m.bearb_id, '') || ' ' ||
                    COALESCE(m.anm_melder, '') || ' ' ||
                    COALESCE(m.anm_bearbeiter, '')), 'A') ||
                setweight(to_tsvector('german', COALESCE(f.ort, '') || ' ' ||
                    COALESCE(f.strasse, '') || ' ' ||
                    COALESCE(f.kreis, '') || ' ' ||
                    COALESCE(f.land, '') || ' ' ||
                    COALESCE(f.amt, '') || ' ' ||
                    COALESCE(f.plz::text, '') || ' ' ||
                    COALESCE(f.mtb, '')), 'B') ||
                setweight(to_tsvector('german', COALESCE(b.beschreibung, '')), 'C') ||
                setweight(to_tsvector('german', COALESCE(u.user_id, '') || ' ' ||
                    COALESCE(u.user_name, '') || ' ' ||
                    COALESCE(u.user_kontakt, '')), 'D') as doc
            FROM 
                meldungen m
            LEFT JOIN 
                fundorte f ON m.fo_zuordnung = f.id
            LEFT JOIN 
                beschreibung b ON f.beschreibung = b.id
            LEFT JOIN 
                melduser mu ON m.id = mu.id_meldung
            LEFT JOIN 
                users u ON mu.id_user = u.id
        """
        
        db.session.execute(text(view_query))
        
        # Create unique index for concurrent refresh
        db.session.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_fts_meldungen_id 
            ON full_text_search (meldungen_id)
        """))
        
        # Create GIN index for full-text search
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_fts_doc_gin 
            ON full_text_search USING gin(doc)
        """))
        
        db.session.commit()
    
    @classmethod
    def refresh_materialized_view(cls):
        """Refresh the materialized view with the latest data using concurrent refresh when possible."""
        try:
            # Try concurrent refresh first
            db.session.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY full_text_search"))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            try:
                # If concurrent refresh fails, try regular refresh in a new transaction
                new_session = db.create_scoped_session()
                try:
                    new_session.execute(text("REFRESH MATERIALIZED VIEW full_text_search"))
                    new_session.commit()
                except Exception as inner_e:
                    new_session.rollback()
                    current_app.logger.error(f"Failed to refresh FTS view: {str(inner_e)}")
                finally:
                    new_session.close()
            except Exception as e:
                current_app.logger.error(f"Failed to refresh FTS view: {str(e)}")

# Set up event listeners for automatic view refresh
def refresh_fts_on_changes(mapper, connection, target):
    """Event listener to refresh FTS view when relevant tables change."""
    try:
        # Create a new session for the refresh operation
        new_session = db.create_scoped_session()
        try:
            FullTextSearch.refresh_materialized_view()
        except Exception as e:
            current_app.logger.error(f"Failed to refresh FTS view on data change: {str(e)}")
        finally:
            new_session.close()
    except Exception as e:
        current_app.logger.error(f"Failed to create new session for FTS refresh: {str(e)}")

# Register the event listeners for all relevant tables
for model in [TblMeldungen, TblFundorte, TblFundortBeschreibung, TblMeldungUser, TblUsers]:
    event.listen(model, 'after_insert', refresh_fts_on_changes)
    event.listen(model, 'after_update', refresh_fts_on_changes)
    event.listen(model, 'after_delete', refresh_fts_on_changes)

# Create DDL event listeners for database initialization
event.listen(
    FullTextSearch.__table__,
    'after_create',
    DDL(
        """
        CREATE INDEX IF NOT EXISTS idx_fts_doc_gin ON full_text_search USING gin(doc);
        """
    )
)
