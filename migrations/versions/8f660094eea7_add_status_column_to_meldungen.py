"""add_status_column_to_meldungen

Adds a status column to track report workflow states.
Migrates existing data from deleted/dat_bear fields to new status field.

Status values:
- OPEN: Report is pending review
- APPR: Report has been approved
- DEL: Report has been soft-deleted
- INFO: Reporter contacted for more info
- UNKL: Report is unclear

Revision ID: 8f660094eea7
Revises: 1aa77659662a
Create Date: 2026-01-13 14:01:47.018770

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8f660094eea7"
down_revision = "1aa77659662a"
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Add the status column with a default value
    # Using nullable=True initially to allow migration of existing data
    op.add_column(
        "meldungen",
        sa.Column("status", sa.String(length=5), nullable=True),
    )

    # Step 2: Migrate existing data based on deleted and dat_bear fields
    # Priority: deleted=True -> DEL, dat_bear IS NOT NULL -> APPR, else -> OPEN
    connection = op.get_bind()

    # First, set deleted records to DEL status
    connection.execute(
        sa.text(
            """
            UPDATE meldungen
            SET status = 'DEL'
            WHERE deleted = TRUE
            """
        )
    )

    # Then, set approved (non-deleted) records to APPR status
    connection.execute(
        sa.text(
            """
            UPDATE meldungen
            SET status = 'APPR'
            WHERE dat_bear IS NOT NULL
            AND (deleted IS NULL OR deleted = FALSE)
            AND status IS NULL
            """
        )
    )

    # Finally, set remaining records to OPEN status
    connection.execute(
        sa.text(
            """
            UPDATE meldungen
            SET status = 'OPEN'
            WHERE status IS NULL
            """
        )
    )

    # Step 3: Make the column non-nullable and add default
    op.alter_column(
        "meldungen",
        "status",
        existing_type=sa.String(length=5),
        nullable=False,
        server_default="OPEN",
    )

    # Step 4: Create an index for better query performance
    op.create_index("ix_meldungen_status", "meldungen", ["status"], unique=False)


def downgrade():
    # Remove index
    op.drop_index("ix_meldungen_status", table_name="meldungen")

    # Remove the status column
    op.drop_column("meldungen", "status")
