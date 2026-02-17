"""add native fts search vector

Revision ID: a90f81bfa252
Revises: a7b8c9d0e1f2
Create Date: 2026-02-17 14:18:18.232204

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TSVECTOR


# revision identifiers, used by Alembic.
revision = 'a90f81bfa252'
down_revision = 'a7b8c9d0e1f2'
branch_labels = None
depends_on = None

# --- SQL for the shared recomputation function ---
# NOTE: PostgreSQL UPDATE...FROM cannot reference the target table alias in
# FROM-clause JOIN conditions. We use a subquery to compute the vector, then
# match back via WHERE m.id = sub.id.
RECOMPUTE_FUNCTION = """
CREATE OR REPLACE FUNCTION recompute_search_vector(target_id integer)
RETURNS void AS $$
BEGIN
    -- Recompute for meldungen that have a fundort
    UPDATE meldungen m
    SET search_vector = sub.sv
    FROM (
        SELECT m2.id,
            setweight(to_tsvector('german',
                coalesce(f.ort, '') || ' ' || coalesce(f.kreis, '') || ' ' ||
                coalesce(f.land, '') || ' ' || coalesce(cast(f.plz as text), '')
            ), 'A') ||
            setweight(to_tsvector('german',
                coalesce(u.user_name, '') || ' ' || coalesce(u.user_kontakt, '') || ' ' ||
                coalesce(u.user_id, '') || ' ' || coalesce(m2.bearb_id, '')
            ), 'B') ||
            setweight(to_tsvector('german',
                coalesce(f.strasse, '') || ' ' || coalesce(f.amt, '') || ' ' ||
                coalesce(f.mtb, '') || ' ' || coalesce(b.beschreibung, '')
            ), 'C') ||
            setweight(to_tsvector('german',
                coalesce(m2.anm_melder, '') || ' ' || coalesce(m2.anm_bearbeiter, '')
            ), 'D') AS sv
        FROM meldungen m2
        JOIN fundorte f ON m2.fo_zuordnung = f.id
        LEFT JOIN beschreibung b ON f.beschreibung = b.id
        LEFT JOIN melduser mu ON m2.id = mu.id_meldung
        LEFT JOIN users u ON mu.id_user = u.id
        WHERE m2.id = target_id
    ) sub
    WHERE m.id = sub.id;

    -- Handle meldungen with no fundorte (fo_zuordnung IS NULL)
    UPDATE meldungen m
    SET search_vector = sub.sv
    FROM (
        SELECT m2.id,
            setweight(to_tsvector('german',
                coalesce(u.user_name, '') || ' ' || coalesce(u.user_kontakt, '') || ' ' ||
                coalesce(u.user_id, '') || ' ' || coalesce(m2.bearb_id, '')
            ), 'B') ||
            setweight(to_tsvector('german',
                coalesce(m2.anm_melder, '') || ' ' || coalesce(m2.anm_bearbeiter, '')
            ), 'D') AS sv
        FROM meldungen m2
        LEFT JOIN melduser mu ON m2.id = mu.id_meldung
        LEFT JOIN users u ON mu.id_user = u.id
        WHERE m2.fo_zuordnung IS NULL
          AND m2.id = target_id
    ) sub
    WHERE m.id = sub.id;
END;
$$ LANGUAGE plpgsql;
"""

# --- Trigger function for meldungen INSERT/UPDATE ---
TRIGGER_MELDUNGEN = """
CREATE OR REPLACE FUNCTION trg_meldungen_search_vector()
RETURNS trigger AS $$
BEGIN
    PERFORM recompute_search_vector(NEW.id);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER meldungen_search_vector_update
    AFTER INSERT OR UPDATE OF bearb_id, anm_melder, anm_bearbeiter, fo_zuordnung
    ON meldungen
    FOR EACH ROW
    EXECUTE FUNCTION trg_meldungen_search_vector();
"""

# --- Trigger function for fundorte UPDATE ---
TRIGGER_FUNDORTE = """
CREATE OR REPLACE FUNCTION trg_fundorte_search_vector()
RETURNS trigger AS $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN SELECT id FROM meldungen WHERE fo_zuordnung = NEW.id LOOP
        PERFORM recompute_search_vector(r.id);
    END LOOP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER fundorte_search_vector_update
    AFTER UPDATE OF ort, strasse, kreis, land, amt, plz, mtb, beschreibung
    ON fundorte
    FOR EACH ROW
    EXECUTE FUNCTION trg_fundorte_search_vector();
"""

# --- Trigger function for beschreibung UPDATE ---
TRIGGER_BESCHREIBUNG = """
CREATE OR REPLACE FUNCTION trg_beschreibung_search_vector()
RETURNS trigger AS $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT m.id FROM meldungen m
        JOIN fundorte f ON m.fo_zuordnung = f.id
        WHERE f.beschreibung = NEW.id
    LOOP
        PERFORM recompute_search_vector(r.id);
    END LOOP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER beschreibung_search_vector_update
    AFTER UPDATE OF beschreibung
    ON beschreibung
    FOR EACH ROW
    EXECUTE FUNCTION trg_beschreibung_search_vector();
"""

# --- Trigger function for melduser INSERT/UPDATE/DELETE ---
TRIGGER_MELDUSER = """
CREATE OR REPLACE FUNCTION trg_melduser_search_vector()
RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        PERFORM recompute_search_vector(OLD.id_meldung);
        RETURN OLD;
    ELSE
        PERFORM recompute_search_vector(NEW.id_meldung);
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER melduser_search_vector_update
    AFTER INSERT OR UPDATE OR DELETE
    ON melduser
    FOR EACH ROW
    EXECUTE FUNCTION trg_melduser_search_vector();
"""

# --- Trigger function for users UPDATE ---
TRIGGER_USERS = """
CREATE OR REPLACE FUNCTION trg_users_search_vector()
RETURNS trigger AS $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN SELECT id_meldung FROM melduser WHERE id_user = NEW.id LOOP
        PERFORM recompute_search_vector(r.id_meldung);
    END LOOP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_search_vector_update
    AFTER UPDATE OF user_name, user_kontakt, user_id
    ON users
    FOR EACH ROW
    EXECUTE FUNCTION trg_users_search_vector();
"""

# --- Backfill: recompute search_vector for all existing rows ---
BACKFILL = """
UPDATE meldungen m
SET search_vector = sub.sv
FROM (
    SELECT m2.id,
        setweight(to_tsvector('german',
            coalesce(f.ort, '') || ' ' || coalesce(f.kreis, '') || ' ' ||
            coalesce(f.land, '') || ' ' || coalesce(cast(f.plz as text), '')
        ), 'A') ||
        setweight(to_tsvector('german',
            coalesce(u.user_name, '') || ' ' || coalesce(u.user_kontakt, '') || ' ' ||
            coalesce(u.user_id, '') || ' ' || coalesce(m2.bearb_id, '')
        ), 'B') ||
        setweight(to_tsvector('german',
            coalesce(f.strasse, '') || ' ' || coalesce(f.amt, '') || ' ' ||
            coalesce(f.mtb, '') || ' ' || coalesce(b.beschreibung, '')
        ), 'C') ||
        setweight(to_tsvector('german',
            coalesce(m2.anm_melder, '') || ' ' || coalesce(m2.anm_bearbeiter, '')
        ), 'D') AS sv
    FROM meldungen m2
    JOIN fundorte f ON m2.fo_zuordnung = f.id
    LEFT JOIN beschreibung b ON f.beschreibung = b.id
    LEFT JOIN melduser mu ON m2.id = mu.id_meldung
    LEFT JOIN users u ON mu.id_user = u.id
) sub
WHERE m.id = sub.id;
"""


def upgrade():
    # 1. Add search_vector column
    op.add_column("meldungen", sa.Column("search_vector", TSVECTOR, nullable=True))

    # 2. Create GIN index
    op.create_index(
        "ix_meldungen_search_vector_gin",
        "meldungen",
        ["search_vector"],
        postgresql_using="gin",
    )

    # 3. Create recomputation function and triggers
    op.execute(RECOMPUTE_FUNCTION)
    op.execute(TRIGGER_MELDUNGEN)
    op.execute(TRIGGER_FUNDORTE)
    op.execute(TRIGGER_BESCHREIBUNG)
    op.execute(TRIGGER_MELDUSER)
    op.execute(TRIGGER_USERS)

    # 4. Backfill existing rows
    op.execute(BACKFILL)

    # 5. Drop the old materialized view
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.full_text_search CASCADE")


def downgrade():
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS meldungen_search_vector_update ON meldungen")
    op.execute("DROP TRIGGER IF EXISTS fundorte_search_vector_update ON fundorte")
    op.execute("DROP TRIGGER IF EXISTS beschreibung_search_vector_update ON beschreibung")
    op.execute("DROP TRIGGER IF EXISTS melduser_search_vector_update ON melduser")
    op.execute("DROP TRIGGER IF EXISTS users_search_vector_update ON users")

    # Drop trigger functions
    op.execute("DROP FUNCTION IF EXISTS trg_meldungen_search_vector()")
    op.execute("DROP FUNCTION IF EXISTS trg_fundorte_search_vector()")
    op.execute("DROP FUNCTION IF EXISTS trg_beschreibung_search_vector()")
    op.execute("DROP FUNCTION IF EXISTS trg_melduser_search_vector()")
    op.execute("DROP FUNCTION IF EXISTS trg_users_search_vector()")
    op.execute("DROP FUNCTION IF EXISTS recompute_search_vector(integer)")

    # Drop index and column
    op.drop_index("ix_meldungen_search_vector_gin", table_name="meldungen")
    op.drop_column("meldungen", "search_vector")
