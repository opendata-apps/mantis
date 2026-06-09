"""rename constraints to naming convention

Aligns all PostgreSQL-default constraint names with the MetaData
naming_convention introduced on the model Base (app/__init__.py), so
future migrations can DROP/ALTER constraints by predictable names.
ALTER TABLE ... RENAME CONSTRAINT is a catalog-only update (instant);
renaming a PK constraint renames its backing index as well.

Revision ID: d7c2a9e41f05
Revises: 3ef7360331ea
Create Date: 2026-06-09 22:05:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "d7c2a9e41f05"
down_revision = "3ef7360331ea"
branch_labels = None
depends_on = None

# (table, historical name, convention name)
RENAMES = [
    ("aemter", "aemter_pkey", "pk_aemter"),
    ("beschreibung", "beschreibung_pkey", "pk_beschreibung"),
    ("users", "users_pkey", "pk_users"),
    ("fundorte", "fundorte_pkey", "pk_fundorte"),
    ("meldungen", "meldungen_pkey", "pk_meldungen"),
    ("melduser", "melduser_pkey", "pk_melduser"),
    ("user_feedback", "user_feedback_pkey", "pk_user_feedback"),
    ("fundorte", "fundorte_beschreibung_fkey", "fk_fundorte_beschreibung_beschreibung"),
    ("meldungen", "meldungen_fo_zuordnung_fkey", "fk_meldungen_fo_zuordnung_fundorte"),
    ("melduser", "melduser_id_finder_fkey", "fk_melduser_id_finder_users"),
    ("melduser", "melduser_id_meldung_fkey", "fk_melduser_id_meldung_meldungen"),
    ("melduser", "melduser_id_user_fkey", "fk_melduser_id_user_users"),
    ("user_feedback", "user_feedback_user_id_fkey", "fk_user_feedback_user_id_users"),
    ("user_feedback", "user_feedback_user_id_key", "uq_user_feedback_user_id"),
    # fk_meldungen_bearb_id_users, uq_users_user_id, uq_melduser_id_meldung
    # (3ef7360331ea) already follow the convention.
]


def upgrade():
    for table, old, new in RENAMES:
        op.execute(f'ALTER TABLE {table} RENAME CONSTRAINT "{old}" TO "{new}"')


def downgrade():
    for table, old, new in RENAMES:
        op.execute(f'ALTER TABLE {table} RENAME CONSTRAINT "{new}" TO "{old}"')
