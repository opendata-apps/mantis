from app import db
from sqlalchemy.orm import relationship


class TblUsers(db.Model):
    """User model for storing reporter and reviewer information.

    Constraints:
        - ix_users_user_id: UNIQUE index on user_id for constraint enforcement
          and fast lookups. Used in 7+ queries across admin, report, provider,
          and statistics routes. Also serves as FK target for meldungen.bearb_id.
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    # UNIQUE on user_id — external-facing identifier (SHA-1 hash or reviewer code).
    # Enables uselist=False relationships (e.g. meldungen.approver) and serves
    # as FK target for meldungen.bearb_id.
    user_id = db.Column(db.String(40), nullable=False, unique=True)
    user_name = db.Column(db.String(45), nullable=False)
    user_rolle = db.Column(db.String(1), nullable=False)
    # Note: user_kontakt is NOT indexed - only used with %text% ILIKE which cannot use B-tree
    user_kontakt = db.Column(db.String(45), nullable=True)

    # Relationship to the feedback source
    feedback_source = relationship(
        "TblUserFeedback",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    reported_links = relationship(
        "TblMeldungUser",
        foreign_keys="[TblMeldungUser.id_user]",
        back_populates="reporter",
        lazy="select",
    )

    found_links = relationship(
        "TblMeldungUser",
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
