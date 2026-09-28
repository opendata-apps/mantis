"""Display and repr behaviour for ``TblUsers`` and ``TblUserFeedback``.

``feedback_source_display`` is what the reviewer modal renders; the reprs are
what a debugging session and the logs show.
"""

from sqlalchemy import select

from app.database.feedback_type import FeedbackSource
from app.database.user_feedback import TblUserFeedback
from app.database.users import TblUsers


def _pick_existing_user(session):
    """Grab the reviewer seeded for the authenticated_client fixture."""
    return session.scalar(select(TblUsers).where(TblUsers.user_id == "9999"))


def test_repr_contains_id_and_name(session):
    user = _pick_existing_user(session)
    rendered = repr(user)
    assert str(user.id) in rendered
    assert user.user_name in rendered


def test_display_name_property_resolves_enum(session):
    user = _pick_existing_user(session)
    feedback = TblUserFeedback(
        user_id=user.id,
        feedback_source=FeedbackSource.FRIENDS.value,
        source_detail=None,
    )
    session.add(feedback)
    session.flush()

    assert feedback.feedback_source_display == "Freunde, Bekannte, Kollegen"


def test_repr_includes_source_code(session):
    user = _pick_existing_user(session)
    feedback = TblUserFeedback(
        user_id=user.id,
        feedback_source=FeedbackSource.TV.value,
    )
    session.add(feedback)
    session.flush()

    rendered = repr(feedback)
    assert "TV" in rendered
    assert str(user.id) in rendered
