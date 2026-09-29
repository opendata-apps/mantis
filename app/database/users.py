from datetime import datetime
from typing import TYPE_CHECKING

from flask_login import UserMixin
from sqlalchemy import CheckConstraint, DateTime, Identity, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.database.meldung_user import TblMeldungUser
    from app.database.user_feedback import TblUserFeedback

from app.extensions import db


class TblUsers(UserMixin, db.Model):
    """User model for storing reporter and reviewer information."""

    __tablename__ = "users"

    __table_args__ = (
        # '1' reporter, '2' finder, '9' reviewer — keep in sync with UserRole
        CheckConstraint("user_rolle IN ('1', '2', '9')", name="user_rolle_valid"),
    )

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    # UNIQUE on user_id — external-facing identifier (SHA-1 hash or reviewer code).
    # Enables uselist=False relationships (e.g. meldungen.approver) and serves
    # as FK target for meldungen.bearb_id.
    user_id: Mapped[str] = mapped_column(String(40), unique=True)
    user_name: Mapped[str] = mapped_column(String(100))
    user_rolle: Mapped[str] = mapped_column(String(1))
    # Note: user_kontakt is NOT indexed - only used with %text% ILIKE which cannot use B-tree
    user_kontakt: Mapped[str | None] = mapped_column(String(254))

    # Audit timestamps: when the row was inserted / last modified via the
    # ORM (bearb_id records who; raw SQL bypasses onupdate).
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship to the feedback source
    feedback_source: Mapped["TblUserFeedback | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    reported_links: Mapped[list["TblMeldungUser"]] = relationship(
        foreign_keys="[TblMeldungUser.id_user]",
        back_populates="reporter",
        lazy="select",
    )

    found_links: Mapped[list["TblMeldungUser"]] = relationship(
        foreign_keys="[TblMeldungUser.id_finder]",
        back_populates="finder",
        lazy="select",
    )

    def get_id(self):
        """The capability token, not the primary key.

        Overrides UserMixin, which would return the guessable ``self.id``.
        """
        return self.user_id

    def __repr__(self):
        return f"<User {self.id} ({self.user_name})>"
