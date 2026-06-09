from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Identity, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import db

if TYPE_CHECKING:
    from app.database.meldung_user import TblMeldungUser
    from app.database.user_feedback import TblUserFeedback


class TblUsers(db.Model):
    """User model for storing reporter and reviewer information.

    Constraints:
        - ix_users_user_id: UNIQUE index on user_id for constraint enforcement
          and fast lookups. Used in 7+ queries across admin, report, provider,
          and statistics routes. Also serves as FK target for meldungen.bearb_id.
    """

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
    user_name: Mapped[str] = mapped_column(String(45))
    user_rolle: Mapped[str] = mapped_column(String(1))
    # Note: user_kontakt is NOT indexed - only used with %text% ILIKE which cannot use B-tree
    user_kontakt: Mapped[str | None] = mapped_column(String(45))

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

    def __repr__(self):
        return f"<User {self.id} ({self.user_name})>"

    def to_dict(self):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "user_kontakt": self.user_kontakt,
            "user_rolle": self.user_rolle,
        }
        if self.feedback_source:
            data["feedback_source"] = self.feedback_source.to_dict()
        return data
