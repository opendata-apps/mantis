"""enforce unique constraints and approver fk

Enforces three schema constraints that were previously application-level only:

1. UNIQUE on users.user_id — allows safe uselist=False relationships
2. UNIQUE on melduser.id_meldung — enforces 1:1 report-to-melduser invariant
3. FK on meldungen.bearb_id -> users.user_id — referential integrity for approver

Revision ID: 3ef7360331ea
Revises: b2c3d4e5f6a7
Create Date: 2026-02-21 00:50:11.499534

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3ef7360331ea'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    # 1a. UNIQUE constraint on users.user_id
    # Drop existing non-unique index, add a unique constraint instead.
    # PostgreSQL automatically creates a unique index to back the constraint,
    # so query performance is preserved.
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index("ix_users_user_id")
        batch_op.create_unique_constraint("uq_users_user_id", ["user_id"])

    # 1b. UNIQUE constraint on melduser.id_meldung
    # The existing composite index (id_meldung, id_user) stays for JOIN optimization.
    # This constraint enforces the 1:1 invariant (one melduser per meldung).
    with op.batch_alter_table("melduser") as batch_op:
        batch_op.create_unique_constraint(
            "uq_melduser_id_meldung", ["id_meldung"]
        )

    # 1c. FK on meldungen.bearb_id -> users.user_id
    # Safety: NULL out orphaned bearb_ids before adding FK
    op.execute(sa.text("""
        UPDATE meldungen
        SET bearb_id = NULL
        WHERE bearb_id IS NOT NULL
          AND bearb_id NOT IN (SELECT user_id FROM users)
    """))

    with op.batch_alter_table("meldungen") as batch_op:
        batch_op.create_foreign_key(
            "fk_meldungen_bearb_id_users",
            "users",
            ["bearb_id"],
            ["user_id"],
        )


def downgrade():
    with op.batch_alter_table("meldungen") as batch_op:
        batch_op.drop_constraint("fk_meldungen_bearb_id_users", type_="foreignkey")

    with op.batch_alter_table("melduser") as batch_op:
        batch_op.drop_constraint("uq_melduser_id_meldung", type_="unique")

    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_constraint("uq_users_user_id", type_="unique")
        batch_op.create_index("ix_users_user_id", ["user_id"], unique=False)
