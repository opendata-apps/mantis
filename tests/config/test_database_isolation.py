from sqlalchemy import select

from app.database.models import TblUsers
from app.extensions import db


def test_commits_stay_inside_the_test_transaction(session):
    user = TblUsers(user_id="isolated-test-user", user_name="Isolation", user_rolle="1")
    session.add(user)
    session.commit()
    query = select(TblUsers.id).where(TblUsers.user_id == user.user_id)
    assert session.scalar(query) == user.id
    with db.engine.connect() as outside_transaction:
        assert outside_transaction.scalar(query) is None


def test_rollback_preserves_prior_commits_and_allows_further_writes(session):
    committed = TblUsers(user_id="before-rollback", user_name="Before", user_rolle="1")
    session.add(committed)
    session.commit()

    session.add(TblUsers(user_id="rolled-back", user_name="Discarded", user_rolle="1"))
    session.flush()
    session.rollback()

    session.add(TblUsers(user_id="after-rollback", user_name="After", user_rolle="1"))
    session.commit()

    query = (
        select(TblUsers.user_id)
        .where(TblUsers.user_id.in_(["before-rollback", "rolled-back", "after-rollback"]))
        .order_by(TblUsers.user_id)
    )
    assert session.scalars(query).all() == ["after-rollback", "before-rollback"]
    with db.engine.connect() as outside_transaction:
        assert outside_transaction.scalars(query).all() == []
