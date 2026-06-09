from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Identity, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import db

if TYPE_CHECKING:
    from app.database.users import TblUsers


class TblUserFeedback(db.Model):
    __tablename__ = "user_feedback"

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    feedback_source: Mapped[str] = mapped_column(String(20))
    source_detail: Mapped[str | None] = mapped_column(String(255))

    # Audit timestamps: when the row was inserted / last modified via the
    # ORM (bearb_id records who; raw SQL bypasses onupdate).
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship back to the user
    user: Mapped["TblUsers"] = relationship(back_populates="feedback_source")

    @property
    def feedback_source_display(self) -> str:
        from app.database.feedback_type import FeedbackSource

        return FeedbackSource.get_display_name(self.feedback_source)

    def __repr__(self):
        return f"<UserFeedback id={self.id} user_id={self.user_id} source='{self.feedback_source}'>"

    def to_dict(self):
        from app.database.feedback_type import FeedbackSource

        return {
            "id": self.id,
            "user_id": self.user_id,
            "feedback_source": self.feedback_source,
            "source_type": FeedbackSource.get_display_name(self.feedback_source),
            "source_detail": self.source_detail,
        }
