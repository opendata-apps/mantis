"""store plz as text

German postal codes are 5-digit identifiers with significant leading
zeros (e.g. 01067 Dresden) — integer storage destroyed them. Converts
fundorte.plz to varchar(5) with a format CHECK. The historical sentinel
plz = 0 ("reporter gave no PLZ", written by the report form) becomes
NULL; the column is now nullable.

The all_data_view materialized view depends on the column and must be
dropped/recreated around the type change. Search vectors are recomputed
because the indexed text for sub-10000 codes changes (e.g. '1067' ->
'01067').

Revision ID: e3a1c5b7d209
Revises: d7c2a9e41f05
Create Date: 2026-06-09 22:30:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e3a1c5b7d209"
down_revision = "d7c2a9e41f05"
branch_labels = None
depends_on = None

DROP_VIEW = 'DROP MATERIALIZED VIEW IF EXISTS public."all_data_view"'

# plz is in this trigger's UPDATE OF list, which blocks ALTER COLUMN TYPE
# ("cannot alter type of a column used in a trigger definition") — the
# trigger is dropped around the type change and recreated identically
# (definition from migration a90f81bfa252).
DROP_FUNDORTE_TRIGGER = "DROP TRIGGER fundorte_search_vector_update ON fundorte"
CREATE_FUNDORTE_TRIGGER = """
CREATE TRIGGER fundorte_search_vector_update
    AFTER UPDATE OF ort, strasse, kreis, land, amt, plz, mtb, beschreibung
    ON fundorte
    FOR EACH ROW
    EXECUTE FUNCTION trg_fundorte_search_vector();
"""

# Same definition as migration b2c3d4e5f6a7 (CREATE_VIEW_WITHOUT_SV).
CREATE_VIEW = """
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

# Set-based recompute of all search vectors for meldungen with a fundort
# (same expression as the a90f81bfa252 backfill).
RECOMPUTE_VECTORS = """
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
WHERE m.id = sub.id
"""


def upgrade():
    op.execute(DROP_VIEW)

    # Fail loudly on out-of-range historical data instead of letting
    # lpad() silently truncate >5-digit values to a passing CHECK.
    op.execute(
        sa.text("""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM fundorte WHERE plz < 0 OR plz > 99999) THEN
                    RAISE EXCEPTION 'fundorte.plz contains values outside 0..99999';
                END IF;
            END
            $$
        """)
    )

    op.execute(DROP_FUNDORTE_TRIGGER)
    op.alter_column("fundorte", "plz", existing_type=sa.Integer(), nullable=True)
    op.execute("""
        ALTER TABLE fundorte
        ALTER COLUMN plz TYPE varchar(5)
        USING CASE WHEN plz = 0 THEN NULL ELSE lpad(plz::text, 5, '0') END
    """)
    op.execute(CREATE_FUNDORTE_TRIGGER)
    op.create_check_constraint(
        "ck_fundorte_plz_format", "fundorte", "plz ~ '^[0-9]{5}$'"
    )

    op.execute(RECOMPUTE_VECTORS)
    op.execute(CREATE_VIEW)


def downgrade():
    op.execute(DROP_VIEW)

    op.drop_constraint("ck_fundorte_plz_format", "fundorte", type_="check")
    # NULL reverts to the historical 0 sentinel; leading zeros are lost
    # again (that is the defect this migration fixes).
    op.execute(DROP_FUNDORTE_TRIGGER)
    op.execute("""
        ALTER TABLE fundorte
        ALTER COLUMN plz TYPE integer
        USING COALESCE(plz::integer, 0)
    """)
    op.execute(CREATE_FUNDORTE_TRIGGER)
    op.alter_column("fundorte", "plz", existing_type=sa.Integer(), nullable=False)

    op.execute(RECOMPUTE_VECTORS)
    op.execute(CREATE_VIEW)
