"""Serialization tests for ``TblUsers`` and ``TblUserFeedback``.

Covers ``to_dict``, ``__repr__``, and the feedback_source join behaviour —
small but critical paths that are used whenever the admin view or the
report API shape user data for JSON output.
"""

from sqlalchemy import select

from app.database.feedback_type import FeedbackSource
from app.database.user_feedback import TblUserFeedback
from app.database.users import TblUsers


def _pick_existing_user(session):
    """Grab the reviewer seeded for the authenticated_client fixture."""
    return session.scalar(select(TblUsers).where(TblUsers.user_id == "9999"))


class TestTblUsersSerialization:
    def test_to_dict_contains_core_fields(self, session):
        user = _pick_existing_user(session)
        assert user is not None

        data = user.to_dict()
        assert data["user_id"] == "9999"
        assert {"id", "user_id", "user_name", "user_kontakt", "user_rolle"} <= set(
            data.keys()
        )

    def test_to_dict_skips_feedback_when_absent(self, session):
        """A user with no feedback row must not include a feedback_source
        key — guards against KeyError in downstream JSON consumers."""
        user = _pick_existing_user(session)
        # Make sure this user has no feedback row in the test DB
        assert user.feedback_source is None

        data = user.to_dict()
        assert "feedback_source" not in data

    def test_to_dict_embeds_feedback_when_present(self, session):
        user = _pick_existing_user(session)
        feedback = TblUserFeedback(
            user_id=user.id,
            feedback_source=FeedbackSource.PRESS.value,
            source_detail="Berliner Zeitung",
        )
        session.add(feedback)
        session.flush()

        data = user.to_dict()
        assert "feedback_source" in data
        assert data["feedback_source"]["feedback_source"] == "PRESS"
        assert data["feedback_source"]["source_type"] == "Presse"
        assert data["feedback_source"]["source_detail"] == "Berliner Zeitung"

    def test_repr_contains_id_and_name(self, session):
        user = _pick_existing_user(session)
        rendered = repr(user)
        assert str(user.id) in rendered
        assert user.user_name in rendered


class TestTblUserFeedbackSerialization:
    def test_to_dict_round_trip(self, session):
        user = _pick_existing_user(session)
        feedback = TblUserFeedback(
            user_id=user.id,
            feedback_source=FeedbackSource.SOCIAL.value,
            source_detail="Instagram",
        )
        session.add(feedback)
        session.flush()

        data = feedback.to_dict()
        assert data["user_id"] == user.id
        assert data["feedback_source"] == "SOCIAL"
        assert data["source_type"] == "Social Media"
        assert data["source_detail"] == "Instagram"

    def test_display_name_property_resolves_enum(self, session):
        user = _pick_existing_user(session)
        feedback = TblUserFeedback(
            user_id=user.id,
            feedback_source=FeedbackSource.FRIENDS.value,
            source_detail=None,
        )
        session.add(feedback)
        session.flush()

        assert feedback.feedback_source_display == "Freunde, Bekannte, Kollegen"

    def test_repr_includes_source_code(self, session):
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
