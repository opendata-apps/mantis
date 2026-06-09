"""add fk on delete behavior

All FKs defaulted to NO ACTION, making user/report deletion fail
opaquely. Deliberate choices:

- user_feedback.user_id -> CASCADE: feedback dies with its user
  (matches the ORM relationship's delete-orphan cascade)
- melduser.id_meldung -> CASCADE: the link row dies with its report
- meldungen.bearb_id -> SET NULL: a report outlives its approver

melduser.id_user/id_finder and meldungen.fo_zuordnung stay NO ACTION on
purpose: a user who reported sightings, and a location in use, must not
be silently deletable.

Revision ID: b6e8a4c2d931
Revises: c9d5f1a3e825
Create Date: 2026-06-10 00:05:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "b6e8a4c2d931"
down_revision = "c9d5f1a3e825"
branch_labels = None
depends_on = None

# (constraint, table, referred table, local cols, remote cols, ondelete)
FKS = [
    (
        "fk_user_feedback_user_id_users",
        "user_feedback",
        "users",
        ["user_id"],
        ["id"],
        "CASCADE",
    ),
    (
        "fk_melduser_id_meldung_meldungen",
        "melduser",
        "meldungen",
        ["id_meldung"],
        ["id"],
        "CASCADE",
    ),
    (
        "fk_meldungen_bearb_id_users",
        "meldungen",
        "users",
        ["bearb_id"],
        ["user_id"],
        "SET NULL",
    ),
]


def upgrade():
    for name, table, ref, cols, refcols, ondelete in FKS:
        op.drop_constraint(name, table, type_="foreignkey")
        op.create_foreign_key(name, table, ref, cols, refcols, ondelete=ondelete)


def downgrade():
    for name, table, ref, cols, refcols, _ in FKS:
        op.drop_constraint(name, table, type_="foreignkey")
        op.create_foreign_key(name, table, ref, cols, refcols)
