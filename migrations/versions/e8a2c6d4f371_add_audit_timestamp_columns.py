"""add audit timestamp columns

No table recorded when a row was inserted or last modified — for a
reviewed scientific dataset that is an accountability gap (bearb_id
records who, nothing recorded when). Adds created_at/updated_at
(timestamptz, NOT NULL, default now()) to the four mutable tables.

Backfill: meldungen.created_at approximates from dat_meld (the
user-facing report date, interpreted as midnight Europe/Berlin);
fundorte inherit their report's created_at. users/user_feedback keep
the migration timestamp — no better signal exists.

Revision ID: e8a2c6d4f371
Revises: d2f6b8a4c159
Create Date: 2026-06-10 00:40:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e8a2c6d4f371"
down_revision = "d2f6b8a4c159"
branch_labels = None
depends_on = None

TABLES = ["meldungen", "fundorte", "users", "user_feedback"]


def upgrade():
    for table in TABLES:
        for col in ("created_at", "updated_at"):
            op.add_column(
                table,
                sa.Column(
                    col,
                    sa.DateTime(timezone=True),
                    server_default=sa.func.now(),
                    nullable=False,
                ),
            )

    op.execute("""
        UPDATE meldungen
        SET created_at = dat_meld::timestamp AT TIME ZONE 'Europe/Berlin',
            updated_at = dat_meld::timestamp AT TIME ZONE 'Europe/Berlin'
        WHERE dat_meld IS NOT NULL
    """)
    op.execute("""
        UPDATE fundorte f
        SET created_at = m.created_at,
            updated_at = m.created_at
        FROM meldungen m
        WHERE m.fo_zuordnung = f.id
    """)


def downgrade():
    for table in TABLES:
        op.drop_column(table, "updated_at")
        op.drop_column(table, "created_at")
