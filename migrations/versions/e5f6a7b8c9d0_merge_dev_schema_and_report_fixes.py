"""Merge the schema branches and remove the experimental geographic scores."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "e5f6a7b8c9d0"
down_revision = ("7e9e54853fa2", "d4e5f6a7b8c9")
branch_labels = None
depends_on = None

CREATE_VIEW = """
CREATE VIEW public.all_data_view AS

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

REPAIR_SEARCH_VECTORS = """
UPDATE meldungen m
SET search_vector = meldung_search_vector(
    m.id, m.fo_zuordnung, m.bearb_id, m.anm_melder, m.anm_bearbeiter)
WHERE m.search_vector IS DISTINCT FROM meldung_search_vector(
    m.id, m.fo_zuordnung, m.bearb_id, m.anm_melder, m.anm_bearbeiter);
"""


def upgrade():
    # Widening users on an existing dev database drops its dependent plain view.
    op.execute("DROP VIEW IF EXISTS public.all_data_view")
    op.execute(CREATE_VIEW)
    op.execute(REPAIR_SEARCH_VECTORS)
    for column in (
        "geo_graded_at",
        "geo_reasons",
        "geo_matched_level",
        "geo_confidence",
        "geo_grade",
    ):
        op.drop_column("fundorte", column)
    op.drop_table("geo_names")


def downgrade():
    op.create_table(
        "geo_names",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("name_norm", sa.Text(), nullable=False),
        sa.Column("ags", sa.BigInteger(), nullable=True),
        sa.Column("kreis", sa.String(100), nullable=True),
        sa.Column("longitude", sa.Double(), nullable=False),
        sa.Column("latitude", sa.Double(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_geo_names")),
    )
    op.create_index("ix_geo_names_name_norm", "geo_names", ["name_norm"])
    op.add_column("fundorte", sa.Column("geo_grade", sa.String(8)))
    op.add_column("fundorte", sa.Column("geo_confidence", sa.Double()))
    op.add_column("fundorte", sa.Column("geo_matched_level", sa.String(12)))
    op.add_column("fundorte", sa.Column("geo_reasons", postgresql.JSONB()))
    op.add_column("fundorte", sa.Column("geo_graded_at", sa.DateTime(timezone=True)))
