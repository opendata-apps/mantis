"""replace matview with plain view

all_data_view materialized a five-table join that runs in single-digit
milliseconds at this data volume (~30k reports). The materialization
bought nothing and cost a refresh-on-read TTL hack in the admin routes,
staleness windows after edits, and manual view management outside
Alembic. A plain view is always fresh and needs no machinery.

Revision ID: a4d8f2b6c573
Revises: f2c8e6a4b513
Create Date: 2026-06-10 01:25:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "a4d8f2b6c573"
down_revision = "f2c8e6a4b513"
branch_labels = None
depends_on = None

VIEW_SELECT = """
SELECT
    m.id AS meldungen_id,
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
    op.execute('DROP MATERIALIZED VIEW IF EXISTS public."all_data_view"')
    op.execute(f'CREATE VIEW public."all_data_view" AS {VIEW_SELECT}')


def downgrade():
    op.execute('DROP VIEW IF EXISTS public."all_data_view"')
    op.execute(f'CREATE MATERIALIZED VIEW public."all_data_view" AS {VIEW_SELECT}')
