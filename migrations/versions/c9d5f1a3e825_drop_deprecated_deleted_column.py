"""drop deprecated deleted column

meldungen.deleted was superseded by the statuses array (DEL status) in
the array migration; since then it was a write-only mirror no query
ever read. The all_data_view materialized view loses the column too.

Revision ID: c9d5f1a3e825
Revises: a8c4e2f6b317
Create Date: 2026-06-09 23:45:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c9d5f1a3e825"
down_revision = "a8c4e2f6b317"
branch_labels = None
depends_on = None

DROP_VIEW = 'DROP MATERIALIZED VIEW IF EXISTS public."all_data_view"'

VIEW_COLUMNS = """
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

CREATE_VIEW = f"""
CREATE MATERIALIZED VIEW public."all_data_view" AS
SELECT
    m.id AS meldungen_id,
{VIEW_COLUMNS}
"""

CREATE_VIEW_WITH_DELETED = f"""
CREATE MATERIALIZED VIEW public."all_data_view" AS
SELECT
    m.id AS meldungen_id,
    m.deleted,
{VIEW_COLUMNS}
"""


def upgrade():
    op.execute(DROP_VIEW)
    op.drop_column("meldungen", "deleted")
    op.execute(CREATE_VIEW)


def downgrade():
    op.execute(DROP_VIEW)
    op.add_column("meldungen", sa.Column("deleted", sa.Boolean(), nullable=True))
    op.execute("UPDATE meldungen SET deleted = ('DEL' = ANY(statuses))")
    op.execute(CREATE_VIEW_WITH_DELETED)
