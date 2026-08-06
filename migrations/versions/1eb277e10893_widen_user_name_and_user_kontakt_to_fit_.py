"""widen user_name and user_kontakt to fit form input limits

Revision ID: 1eb277e10893
Revises: 3ef7360331ea
Create Date: 2026-08-06 17:43:20.775349

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1eb277e10893"
down_revision = "3ef7360331ea"
branch_labels = None
depends_on = None


# Two objects reference these columns and block ALTER TYPE:
#  - all_data_view (materialized) — recreated by the app after upgrade
#    (`flask create_all_data_view` / test seeding), per the repo pattern.
#  - users_search_vector_update trigger (from a90f81bfa252) — its function
#    survives; only the trigger must be dropped and restored around the ALTER.
_USERS_SEARCH_TRIGGER = """
CREATE TRIGGER users_search_vector_update
    AFTER UPDATE OF user_name, user_kontakt, user_id
    ON users
    FOR EACH ROW
    EXECUTE FUNCTION trg_users_search_vector()
"""


def _widen(user_name_len, user_kontakt_len, old_name_len, old_kontakt_len):
    op.execute('DROP MATERIALIZED VIEW IF EXISTS public."all_data_view" CASCADE')
    op.execute("DROP TRIGGER IF EXISTS users_search_vector_update ON users")
    op.alter_column(
        "users",
        "user_name",
        type_=sa.String(user_name_len),
        existing_type=sa.String(old_name_len),
        existing_nullable=False,
    )
    op.alter_column(
        "users",
        "user_kontakt",
        type_=sa.String(user_kontakt_len),
        existing_type=sa.String(old_kontakt_len),
        existing_nullable=True,
    )
    op.execute(_USERS_SEARCH_TRIGGER)


def upgrade():
    # Form accepts email up to 120 chars and names up to 50, but both columns
    # were varchar(45) — long values raised StringDataRightTruncation and lost
    # the report (500). user_name stores "Lastname X." so 50-char surnames need
    # >45. Widening a varchar length in PostgreSQL is catalog-only: no rewrite.
    _widen(100, 254, 45, 45)


def downgrade():
    _widen(45, 45, 100, 254)
