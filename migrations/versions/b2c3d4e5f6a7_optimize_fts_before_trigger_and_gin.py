"""optimize fts: before trigger, fastupdate off, view cleanup

Fixes three performance issues in the FTS infrastructure:
1. Converts meldungen trigger from AFTER to BEFORE to avoid double-write per INSERT/UPDATE
2. Recreates GIN index with fastupdate=off for deterministic read latency
3. Removes search_vector from all_data_view (join to meldungen instead)

Revision ID: b2c3d4e5f6a7
Revises: a90f81bfa252
Create Date: 2026-02-17 14:51:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a90f81bfa252'
branch_labels = None
depends_on = None

# --- New BEFORE trigger function for meldungen ---
# Sets NEW.search_vector directly, avoiding the double-write of AFTER + UPDATE.
# Other table triggers (fundorte, beschreibung, melduser, users) remain AFTER
# triggers that call recompute_search_vector() — which updates search_vector
# directly and does NOT re-fire this BEFORE trigger (it only triggers on
# UPDATE OF bearb_id, anm_melder, anm_bearbeiter, fo_zuordnung).
BEFORE_TRIGGER_MELDUNGEN = """
CREATE OR REPLACE FUNCTION trg_meldungen_search_vector()
RETURNS trigger AS $$
DECLARE
    f_ort text := '';
    f_kreis text := '';
    f_land text := '';
    f_plz text := '';
    f_strasse text := '';
    f_amt text := '';
    f_mtb text := '';
    f_beschreibung text := '';
    u_name text := '';
    u_kontakt text := '';
    u_uid text := '';
BEGIN
    -- Fetch fundort + beschreibung data if linked
    IF NEW.fo_zuordnung IS NOT NULL THEN
        SELECT
            coalesce(f.ort, ''), coalesce(f.kreis, ''), coalesce(f.land, ''),
            coalesce(cast(f.plz as text), ''),
            coalesce(f.strasse, ''), coalesce(f.amt, ''), coalesce(f.mtb, ''),
            coalesce(b.beschreibung, '')
        INTO f_ort, f_kreis, f_land, f_plz, f_strasse, f_amt, f_mtb, f_beschreibung
        FROM fundorte f
        LEFT JOIN beschreibung b ON f.beschreibung = b.id
        WHERE f.id = NEW.fo_zuordnung;
    END IF;

    -- Fetch user data (won't exist during INSERT — melduser trigger handles that later)
    SELECT coalesce(u.user_name, ''), coalesce(u.user_kontakt, ''), coalesce(u.user_id, '')
    INTO u_name, u_kontakt, u_uid
    FROM melduser mu
    JOIN users u ON mu.id_user = u.id
    WHERE mu.id_meldung = NEW.id
    LIMIT 1;

    -- Build weighted search vector and assign directly to NEW row
    NEW.search_vector :=
        setweight(to_tsvector('german',
            f_ort || ' ' || f_kreis || ' ' || f_land || ' ' || f_plz
        ), 'A') ||
        setweight(to_tsvector('german',
            u_name || ' ' || u_kontakt || ' ' || u_uid || ' ' || coalesce(NEW.bearb_id, '')
        ), 'B') ||
        setweight(to_tsvector('german',
            f_strasse || ' ' || f_amt || ' ' || f_mtb || ' ' || f_beschreibung
        ), 'C') ||
        setweight(to_tsvector('german',
            coalesce(NEW.anm_melder, '') || ' ' || coalesce(NEW.anm_bearbeiter, '')
        ), 'D');

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER meldungen_search_vector_update
    BEFORE INSERT OR UPDATE OF bearb_id, anm_melder, anm_bearbeiter, fo_zuordnung
    ON meldungen
    FOR EACH ROW
    EXECUTE FUNCTION trg_meldungen_search_vector();
"""

# --- Restore old AFTER trigger (for downgrade) ---
AFTER_TRIGGER_MELDUNGEN = """
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

# --- Materialized view WITHOUT search_vector ---
CREATE_VIEW_WITHOUT_SV = """
CREATE MATERIALIZED VIEW public."all_data_view" AS
SELECT
    m.id AS meldungen_id,
    m.deleted,
    m.statuses,
    m.dat_fund_von,
    m.dat_fund_bis,
    m.dat_meld,
    m.dat_bear,
    m.bearb_id,
    m.tiere,
    m.art_m,
    m.art_w,
    m.art_n,
    m.art_o,
    m.art_f,
    m.fo_zuordnung,
    m.fo_quelle,
    m.fo_beleg,
    m.anm_melder,
    m.anm_bearbeiter,
    f.id AS fundorte_id,
    f.plz,
    f.ort,
    f.strasse,
    f.kreis,
    f.land,
    f.amt,
    f.mtb,
    f.longitude,
    f.latitude,
    f.ablage,
    b.id AS beschreibung_id,
    b.beschreibung,
    mu.id_meldung,
    mu.id_user,
    mu.id_finder,
    u.id AS user_tbl_id,
    u.user_id,
    u.user_name,
    u.user_kontakt
FROM meldungen m
LEFT JOIN fundorte f ON m.fo_zuordnung = f.id
LEFT JOIN beschreibung b ON f.beschreibung = b.id
LEFT JOIN melduser mu ON m.id = mu.id_meldung
LEFT JOIN users u ON mu.id_user = u.id
"""

# --- Materialized view WITH search_vector (for downgrade) ---
CREATE_VIEW_WITH_SV = """
CREATE MATERIALIZED VIEW public."all_data_view" AS
SELECT
    m.id AS meldungen_id,
    m.deleted,
    m.statuses,
    m.dat_fund_von,
    m.dat_fund_bis,
    m.dat_meld,
    m.dat_bear,
    m.bearb_id,
    m.tiere,
    m.art_m,
    m.art_w,
    m.art_n,
    m.art_o,
    m.art_f,
    m.fo_zuordnung,
    m.fo_quelle,
    m.fo_beleg,
    m.anm_melder,
    m.anm_bearbeiter,
    m.search_vector,
    f.id AS fundorte_id,
    f.plz,
    f.ort,
    f.strasse,
    f.kreis,
    f.land,
    f.amt,
    f.mtb,
    f.longitude,
    f.latitude,
    f.ablage,
    b.id AS beschreibung_id,
    b.beschreibung,
    mu.id_meldung,
    mu.id_user,
    mu.id_finder,
    u.id AS user_tbl_id,
    u.user_id,
    u.user_name,
    u.user_kontakt
FROM meldungen m
LEFT JOIN fundorte f ON m.fo_zuordnung = f.id
LEFT JOIN beschreibung b ON f.beschreibung = b.id
LEFT JOIN melduser mu ON m.id = mu.id_meldung
LEFT JOIN users u ON mu.id_user = u.id
"""


def upgrade():
    # 1. Replace meldungen AFTER trigger with BEFORE trigger
    op.execute("DROP TRIGGER IF EXISTS meldungen_search_vector_update ON meldungen")
    op.execute("DROP FUNCTION IF EXISTS trg_meldungen_search_vector()")
    op.execute(BEFORE_TRIGGER_MELDUNGEN)

    # 2. Recreate GIN index with fastupdate=off
    op.execute("DROP INDEX IF EXISTS ix_meldungen_search_vector_gin")
    op.execute("""
        CREATE INDEX ix_meldungen_search_vector_gin
        ON meldungen USING gin (search_vector)
        WITH (fastupdate = off)
    """)

    # 3. Recreate materialized view without search_vector
    op.execute('DROP MATERIALIZED VIEW IF EXISTS public."all_data_view"')
    op.execute(CREATE_VIEW_WITHOUT_SV)


def downgrade():
    # 1. Restore AFTER trigger
    op.execute("DROP TRIGGER IF EXISTS meldungen_search_vector_update ON meldungen")
    op.execute("DROP FUNCTION IF EXISTS trg_meldungen_search_vector()")
    op.execute(AFTER_TRIGGER_MELDUNGEN)

    # 2. Recreate GIN index without fastupdate option
    op.execute("DROP INDEX IF EXISTS ix_meldungen_search_vector_gin")
    op.execute("""
        CREATE INDEX ix_meldungen_search_vector_gin
        ON meldungen USING gin (search_vector)
    """)

    # 3. Restore materialized view with search_vector
    op.execute('DROP MATERIALIZED VIEW IF EXISTS public."all_data_view"')
    op.execute(CREATE_VIEW_WITH_SV)
