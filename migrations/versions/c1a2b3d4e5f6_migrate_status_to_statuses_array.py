"""migrate_status_to_statuses_array

Migrates from single status column to multi-select statuses array.

This enables reports to have multiple statuses simultaneously, e.g.:
- [OPEN, INFO] - Open and contacted for info
- [APPR, UNKL] - Approved but was unclear

Status categories:
- Workflow states (mutually exclusive): OPEN, APPR, DEL
- Flags (can combine with workflow states): INFO, UNKL

Revision ID: c1a2b3d4e5f6
Revises: b426f6a748b3
Create Date: 2026-01-27 18:45:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "c1a2b3d4e5f6"
down_revision = "b426f6a748b3"
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Add the statuses array column as nullable initially
    op.add_column(
        "meldungen",
        sa.Column("statuses", postgresql.ARRAY(sa.String(length=5)), nullable=True),
    )

    # Step 2: Migrate existing data - convert single status to array
    connection = op.get_bind()

    # Convert each single status value to a single-element array
    connection.execute(
        sa.text(
            """
            UPDATE meldungen
            SET statuses = ARRAY[status]
            WHERE status IS NOT NULL
            """
        )
    )

    # Handle any NULL status values (shouldn't exist, but be safe)
    connection.execute(
        sa.text(
            """
            UPDATE meldungen
            SET statuses = ARRAY['OPEN']
            WHERE statuses IS NULL
            """
        )
    )

    # Step 3: Make the column non-nullable with server default
    op.alter_column(
        "meldungen",
        "statuses",
        existing_type=postgresql.ARRAY(sa.String(length=5)),
        nullable=False,
        server_default="{OPEN}",
    )

    # Step 4: Create GIN index for array containment queries
    # GIN is optimal for: statuses @> '{APPR}' (contains)
    op.create_index(
        "ix_meldungen_statuses_gin",
        "meldungen",
        ["statuses"],
        unique=False,
        postgresql_using="gin",
    )

    # Step 5: Drop old indexes that reference the status column
    # The composite index is no longer useful with array column
    op.drop_index("ix_meldungen_status_dat_fund_von", table_name="meldungen")
    op.drop_index("ix_meldungen_status", table_name="meldungen")

    # Step 6: Drop the old status column
    # First remove the server_default
    op.alter_column(
        "meldungen",
        "status",
        server_default=None,
    )
    op.drop_column("meldungen", "status")


def downgrade():
    # Step 1: Re-add the status column
    op.add_column(
        "meldungen",
        sa.Column("status", sa.String(length=5), nullable=True),
    )

    # Step 2: Migrate data back - take first workflow state from array
    # Priority: DEL > APPR > OPEN (workflow states only)
    connection = op.get_bind()

    # Set DEL status for records containing DEL
    connection.execute(
        sa.text(
            """
            UPDATE meldungen
            SET status = 'DEL'
            WHERE 'DEL' = ANY(statuses)
            """
        )
    )

    # Set APPR status for records containing APPR (not already set)
    connection.execute(
        sa.text(
            """
            UPDATE meldungen
            SET status = 'APPR'
            WHERE 'APPR' = ANY(statuses)
            AND status IS NULL
            """
        )
    )

    # Set OPEN for remaining (or any that only have flags)
    connection.execute(
        sa.text(
            """
            UPDATE meldungen
            SET status = 'OPEN'
            WHERE status IS NULL
            """
        )
    )

    # Step 3: Make status non-nullable with default
    op.alter_column(
        "meldungen",
        "status",
        existing_type=sa.String(length=5),
        nullable=False,
        server_default="OPEN",
    )

    # Step 4: Recreate original indexes
    op.create_index("ix_meldungen_status", "meldungen", ["status"], unique=False)
    op.create_index(
        "ix_meldungen_status_dat_fund_von",
        "meldungen",
        ["status", "dat_fund_von"],
        unique=False,
    )

    # Step 5: Drop the GIN index
    op.drop_index("ix_meldungen_statuses_gin", table_name="meldungen")

    # Step 6: Drop the statuses array column
    op.alter_column("meldungen", "statuses", server_default=None)
    op.drop_column("meldungen", "statuses")
