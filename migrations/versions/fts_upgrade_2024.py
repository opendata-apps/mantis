"""Upgrade FTS implementation

Revision ID: fts_upgrade_2024
Revises: 
Create Date: 2024-01-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TSVECTOR

# revision identifiers, used by Alembic.
revision = 'fts_upgrade_2024'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    
    # Drop the old index if it exists
    conn.execute(sa.text('DROP INDEX IF EXISTS idx_full_text_search'))
    conn.execute(sa.text('DROP INDEX IF EXISTS idx_fts_doc_gin'))
    conn.execute(sa.text('DROP INDEX IF EXISTS idx_fts_meldungen_id'))
    
    # Drop the old materialized view
    conn.execute(sa.text('DROP MATERIALIZED VIEW IF EXISTS full_text_search'))
    
    # Create the new materialized view with improved structure
    conn.execute(sa.text("""
        CREATE MATERIALIZED VIEW full_text_search AS
        SELECT 
            m.id as meldungen_id,
            to_tsvector('german',
                COALESCE(m.bearb_id, '') || ' ' ||
                COALESCE(m.anm_melder, '') || ' ' ||
                COALESCE(m.anm_bearbeiter, '') || ' ' ||
                COALESCE(f.ort, '') || ' ' ||
                COALESCE(f.strasse, '') || ' ' ||
                COALESCE(f.kreis, '') || ' ' ||
                COALESCE(f.land, '') || ' ' ||
                COALESCE(f.amt, '') || ' ' ||
                COALESCE(f.plz::text, '') || ' ' ||
                COALESCE(f.mtb, '') || ' ' ||
                COALESCE(b.beschreibung, '') || ' ' ||
                COALESCE(mu.id_user::text, '') || ' ' ||
                COALESCE(mu.id_finder::text, '') || ' ' ||
                COALESCE(u.user_id, '') || ' ' ||
                COALESCE(u.user_name, '') || ' ' ||
                COALESCE(u.user_kontakt, '')
            ) as doc
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
    """))
    
    # Create a unique index on meldungen_id
    conn.execute(sa.text("""
        CREATE UNIQUE INDEX idx_fts_meldungen_id ON full_text_search (meldungen_id)
    """))
    
    # Create the GIN index for full-text search
    conn.execute(sa.text("""
        CREATE INDEX idx_fts_doc_gin ON full_text_search USING gin(doc)
    """))

def downgrade():
    conn = op.get_bind()
    
    # Drop all indexes
    conn.execute(sa.text('DROP INDEX IF EXISTS idx_fts_doc_gin'))
    conn.execute(sa.text('DROP INDEX IF EXISTS idx_fts_meldungen_id'))
    conn.execute(sa.text('DROP INDEX IF EXISTS idx_full_text_search'))
    
    # Drop the materialized view
    conn.execute(sa.text('DROP MATERIALIZED VIEW IF EXISTS full_text_search'))
    
    # Recreate the old materialized view and index (if needed)
    conn.execute(sa.text("""
        CREATE MATERIALIZED VIEW full_text_search AS
        SELECT 
            m.id as meldungen_id,
            to_tsvector('german',
                COALESCE(m.bearb_id, '') || ' ' ||
                COALESCE(m.anm_melder, '') || ' ' ||
                COALESCE(m.anm_bearbeiter, '') || ' ' ||
                COALESCE(f.ort, '') || ' ' ||
                COALESCE(f.strasse, '') || ' ' ||
                COALESCE(f.kreis, '') || ' ' ||
                COALESCE(f.land, '') || ' ' ||
                COALESCE(f.amt, '') || ' ' ||
                COALESCE(f.plz::text, '') || ' ' ||
                COALESCE(f.mtb, '') || ' ' ||
                COALESCE(b.beschreibung, '') || ' ' ||
                COALESCE(mu.id_user::text, '') || ' ' ||
                COALESCE(mu.id_finder::text, '') || ' ' ||
                COALESCE(u.user_id, '') || ' ' ||
                COALESCE(u.user_name, '') || ' ' ||
                COALESCE(u.user_kontakt, '')
            ) as doc
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
    """))
    
    conn.execute(sa.text("""
        CREATE INDEX idx_full_text_search ON full_text_search USING gin(doc)
    """)) 