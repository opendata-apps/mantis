"""enforce status combinations

ReportStatus.validate_combination() has enforced these rules in Python
since the statuses-array migration, but the database accepted anything.
Legal combinations (exactly these six):

    {OPEN}, {OPEN,INFO}, {OPEN,UNKL}, {OPEN,INFO,UNKL}, {APPR}, {DEL}

Historical data predating the tightened rules is normalized first:
- DEL is exclusive: any array containing DEL collapses to {DEL}
- APPR is exclusive ("approval resolves all active concerns"): any
  array containing APPR collapses to {APPR} — drops stale UNKL/INFO
  flags on approved rows (e.g. {APPR,UNKL}, which the original array
  migration still documented as legal)
- bare flags ({INFO}, {UNKL}) gain the OPEN workflow state

Unknown status values are NOT silently repaired — adding the CHECK
fails loudly if any remain.

Revision ID: a8c4e2f6b317
Revises: f4b8d2c6e017
Create Date: 2026-06-09 23:20:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "a8c4e2f6b317"
down_revision = "f4b8d2c6e017"
branch_labels = None
depends_on = None

STATUSES_VALID = (
    "statuses = '{APPR}'::varchar[] "
    "OR statuses = '{DEL}'::varchar[] "
    "OR ('OPEN' = ANY(statuses) AND statuses <@ '{OPEN,INFO,UNKL}'::varchar[])"
)


def upgrade():
    # Order matters: DEL wins over APPR for rows carrying both.
    op.execute("""
        UPDATE meldungen SET statuses = '{DEL}'
        WHERE 'DEL' = ANY(statuses) AND statuses <> '{DEL}'
    """)
    op.execute("""
        UPDATE meldungen SET statuses = '{APPR}'
        WHERE 'APPR' = ANY(statuses) AND statuses <> '{APPR}'
    """)
    op.execute("""
        UPDATE meldungen SET statuses = array_prepend('OPEN'::varchar, statuses)
        WHERE NOT (statuses && '{OPEN,APPR,DEL}'::varchar[])
    """)

    op.create_check_constraint(
        "ck_meldungen_statuses_valid", "meldungen", STATUSES_VALID
    )


def downgrade():
    # The data normalization is intentionally not reversed.
    op.drop_constraint("ck_meldungen_statuses_valid", "meldungen", type_="check")
