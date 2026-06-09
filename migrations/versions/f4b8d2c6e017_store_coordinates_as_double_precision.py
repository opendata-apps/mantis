"""store coordinates as double precision

fundorte.latitude/longitude were varchar(25): no range enforcement, no
SQL math, lexicographic ordering, and format drift (comma decimal
separators) that required a normalize-coordinates CLI command. Double
precision exceeds GPS accuracy by many orders of magnitude and lets the
database enforce coordinate ranges via CHECK constraints.

The USING clause tolerates the known legacy formats (whitespace, comma
separator); anything else fails the cast loudly rather than being
silently mangled.

Revision ID: f4b8d2c6e017
Revises: e3a1c5b7d209
Create Date: 2026-06-09 22:55:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "f4b8d2c6e017"
down_revision = "e3a1c5b7d209"
branch_labels = None
depends_on = None

DROP_VIEW = 'DROP MATERIALIZED VIEW IF EXISTS public."all_data_view"'

# Same definition as migration b2c3d4e5f6a7 (CREATE_VIEW_WITHOUT_SV);
# latitude/longitude become double precision via the base table.
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


def upgrade():
    op.execute(DROP_VIEW)

    for col in ("latitude", "longitude"):
        op.execute(f"""
            ALTER TABLE fundorte
            ALTER COLUMN {col} TYPE double precision
            USING replace(btrim({col}), ',', '.')::double precision
        """)

    op.create_check_constraint(
        "ck_fundorte_latitude_range", "fundorte", "latitude BETWEEN -90 AND 90"
    )
    op.create_check_constraint(
        "ck_fundorte_longitude_range", "fundorte", "longitude BETWEEN -180 AND 180"
    )

    op.execute(CREATE_VIEW)


def downgrade():
    op.execute(DROP_VIEW)

    op.drop_constraint("ck_fundorte_latitude_range", "fundorte", type_="check")
    op.drop_constraint("ck_fundorte_longitude_range", "fundorte", type_="check")

    for col in ("latitude", "longitude"):
        op.execute(f"""
            ALTER TABLE fundorte
            ALTER COLUMN {col} TYPE varchar(25)
            USING {col}::text
        """)

    op.execute(CREATE_VIEW)
