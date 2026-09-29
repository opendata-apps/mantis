"""constrain user_rolle values

users.user_rolle held magic one-character strings with no DB-level
documentation of the legal set. Production data showed role '2'
(finder), which the UserRole enum did not even define — the enum gains
FINDER and the database now enforces the full set.

Revision ID: f2c8e6a4b513
Revises: e8a2c6d4f371
Create Date: 2026-06-10 00:55:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "f2c8e6a4b513"
down_revision = "e8a2c6d4f371"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        DO $$
        DECLARE offenders text;
        BEGIN
            SELECT string_agg(format('%s (%L)', id, user_rolle), ', ' ORDER BY id)
              INTO offenders
              FROM users
             WHERE user_rolle NOT IN ('1', '2', '9');
            IF offenders IS NOT NULL THEN
                RAISE EXCEPTION 'users.user_rolle is not a known role in: %', offenders
                    USING HINT = 'Repair or remove these rows, then re-run the migration.';
            END IF;
        END
        $$
    """)

    # '1' reporter, '2' finder, '9' reviewer (UserRole enum)
    op.create_check_constraint(
        op.f("ck_users_user_rolle_valid"), "users", "user_rolle IN ('1', '2', '9')"
    )


def downgrade():
    op.drop_constraint(op.f("ck_users_user_rolle_valid"), "users", type_="check")
