"""migrate feedback types to enum

Replace feedback_types lookup table with FeedbackSource StrEnum.
Stores enum values directly as VARCHAR in user_feedback.feedback_source.

Revision ID: a7b8c9d0e1f2
Revises: c1a2b3d4e5f6
Create Date: 2026-02-17 11:30:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a7b8c9d0e1f2"
down_revision = "c1a2b3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add new feedback_source column (nullable initially for backfill)
    op.add_column(
        "user_feedback", sa.Column("feedback_source", sa.String(20), nullable=True)
    )

    # 2. Backfill: map feedback_type_id → enum value
    op.execute(
        """
        UPDATE user_feedback SET feedback_source = CASE feedback_type_id
            WHEN 1 THEN 'EVENT'
            WHEN 2 THEN 'FLYER'
            WHEN 3 THEN 'PRESS'
            WHEN 4 THEN 'TV'
            WHEN 5 THEN 'INTERNET'
            WHEN 6 THEN 'SOCIAL'
            WHEN 7 THEN 'FRIENDS'
            WHEN 8 THEN 'OTHER'
            ELSE 'OTHER'
        END
        """
    )

    # 3. Make feedback_source NOT NULL now that all rows are backfilled
    op.alter_column("user_feedback", "feedback_source", nullable=False)

    # 4. Drop FK column (also drops the foreign key constraint)
    op.drop_constraint(
        "user_feedback_feedback_type_id_fkey", "user_feedback", type_="foreignkey"
    )
    op.drop_column("user_feedback", "feedback_type_id")

    # 5. Drop the lookup table
    op.drop_table("feedback_types")


def downgrade():
    # Recreate lookup table
    op.create_table(
        "feedback_types",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # Seed lookup table
    op.execute(
        """
        INSERT INTO feedback_types (id, name) VALUES
            (1, 'Auf einer Veranstaltung'),
            (2, 'Flyer/ Folder des Projektes'),
            (3, 'Presse'),
            (4, 'Fernsehbeitrag'),
            (5, 'Internetrecherche'),
            (6, 'Social Media'),
            (7, 'Freunde, Bekannte, Kollegen'),
            (8, 'Andere')
        """
    )

    # Recreate FK column
    op.add_column(
        "user_feedback",
        sa.Column("feedback_type_id", sa.Integer(), nullable=True),
    )

    # Backfill reverse: enum value → FK id
    op.execute(
        """
        UPDATE user_feedback SET feedback_type_id = CASE feedback_source
            WHEN 'EVENT' THEN 1
            WHEN 'FLYER' THEN 2
            WHEN 'PRESS' THEN 3
            WHEN 'TV' THEN 4
            WHEN 'INTERNET' THEN 5
            WHEN 'SOCIAL' THEN 6
            WHEN 'FRIENDS' THEN 7
            WHEN 'OTHER' THEN 8
            ELSE 8
        END
        """
    )

    op.alter_column("user_feedback", "feedback_type_id", nullable=False)
    op.create_foreign_key(
        "user_feedback_feedback_type_id_fkey",
        "user_feedback",
        "feedback_types",
        ["feedback_type_id"],
        ["id"],
    )

    # Drop the enum column
    op.drop_column("user_feedback", "feedback_source")
