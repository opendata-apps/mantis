"""Upgrade FTS to weighted search implementation

Revision ID: fts_weighted_upgrade_2024
Revises: fts_upgrade_2024
Create Date: 2024-01-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TSVECTOR

# revision identifiers, used by Alembic.
revision = 'fts_weighted_upgrade_2024'
down_revision = 'fts_upgrade_2024'
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    
    # Drop existing indexes first
    conn.execute(sa.text('DROP INDEX IF EXISTS idx_fts_doc_gin'))
    conn.execute(sa.text('DROP INDEX IF EXISTS idx_fts_meldungen_id'))
    
    # Drop the existing materialized view
    conn.execute(sa.text('DROP MATERIALIZED VIEW IF EXISTS full_text_search'))
    
    # Create the new materialized view with weighted search
    conn.execute(sa.text("""
        CREATE MATERIALIZED VIEW full_text_search AS
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
    """))
    
    # Create the indexes
    conn.execute(sa.text("""
        CREATE UNIQUE INDEX idx_fts_meldungen_id 
        ON full_text_search (meldungen_id)
    """))
    
    conn.execute(sa.text("""
        CREATE INDEX idx_fts_doc_gin 
        ON full_text_search USING gin(doc)
    """))

def downgrade():
    conn = op.get_bind()
    
    # Drop the weighted search indexes
    conn.execute(sa.text('DROP INDEX IF EXISTS idx_fts_doc_gin'))
    conn.execute(sa.text('DROP INDEX IF EXISTS idx_fts_meldungen_id'))
    
    # Drop the weighted search materialized view
    conn.execute(sa.text('DROP MATERIALIZED VIEW IF EXISTS full_text_search'))
    
    # Recreate the original materialized view
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
    
    # Recreate the original indexes
    conn.execute(sa.text("""
        CREATE UNIQUE INDEX idx_fts_meldungen_id 
        ON full_text_search (meldungen_id)
    """))
    
    conn.execute(sa.text("""
        CREATE INDEX idx_fts_doc_gin 
        ON full_text_search USING gin(doc)
    """)) 