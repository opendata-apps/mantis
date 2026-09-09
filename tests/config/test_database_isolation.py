import pytest
from sqlalchemy import select

from app.database.models import TblMeldungen, TblUsers
from app.extensions import db


@pytest.mark.parametrize("name", ["First test", "Second test"])
def test_database_resets_between_tests(app, session, name):
    query = select(TblUsers.id).where(TblUsers.user_id == "isolated-test-user")
    assert session.scalar(query) is None
    user = TblUsers(user_id="isolated-test-user", user_name=name, user_rolle="1")
    session.add(user)
    session.commit()
    assert session.scalar(query) == user.id
    with app.app_context(), db.engine.connect() as outside_transaction:
        assert outside_transaction.scalar(query) == user.id


def test_rollback_preserves_prior_commits_and_allows_further_writes(app, session):
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
        .where(
            TblUsers.user_id.in_(["before-rollback", "rolled-back", "after-rollback"])
        )
        .order_by(TblUsers.user_id)
    )
    assert session.scalars(query).all() == ["after-rollback", "before-rollback"]
    with app.app_context(), db.engine.connect() as outside_transaction:
        assert outside_transaction.scalars(query).all() == [
            "after-rollback",
            "before-rollback",
        ]


def test_test_session_rollback_preserves_a_request_commit(
    session, authenticated_client
):
    query = select(TblMeldungen.anm_bearbeiter).where(TblMeldungen.id == 1)
    assert session.scalar(query) != "Committed by request"
    response = authenticated_client.post(
        "/change_mantis_meta_data/1",
        data={"type": "anm_bearbeiter", "new_data": "Committed by request"},
    )
    assert response.status_code == 200
    assert session.scalar(query) == "Committed by request"

    session.rollback()

    assert session.scalar(query) == "Committed by request"
