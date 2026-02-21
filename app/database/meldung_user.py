from sqlalchemy import Index
from sqlalchemy.orm import relationship

from app import db


class TblMeldungUser(db.Model):
    """Junction table linking reports (meldungen) to users.

    Indexes:
        - ix_melduser_id_meldung_id_user: Composite index for JOIN operations.
          Query patterns:
            JOIN TblMeldungUser ON TblMeldungen.id == TblMeldungUser.id_meldung
            JOIN TblUsers ON TblMeldungUser.id_user == TblUsers.id

    Note: PostgreSQL does NOT auto-create indexes on foreign keys.
    Every admin/provider/reviewer query joins through this table.
    """

    __tablename__ = "melduser"

    # Composite index for the typical join pattern
    # Per PostgreSQL docs: column order should match query join order
    # Queries join: meldungen.id -> melduser.id_meldung -> melduser.id_user -> users.id
    __table_args__ = (
        Index("ix_melduser_id_meldung_id_user", "id_meldung", "id_user"),
    )

    id = db.Column(db.Integer, primary_key=True)
    # FK to meldungen - used in every JOIN operation.
    # UNIQUE enforces the 1:1 invariant: one melduser row per meldung.
    id_meldung = db.Column(
        db.Integer, db.ForeignKey("meldungen.id"), unique=True, nullable=False
    )
    # FK to users - used in every JOIN operation
    id_user = db.Column(
        db.Integer, db.ForeignKey("users.id"), unique=False, nullable=False
    )
    # FK to finder (optional) - not frequently queried, no index needed
    id_finder = db.Column(
        db.Integer, db.ForeignKey("users.id"), unique=False, nullable=True
    )

    # --- Relationships ---
    meldung = relationship(
        "TblMeldungen",
        foreign_keys=[id_meldung],
        back_populates="reporter_link",
        lazy="select",
    )

    reporter = relationship(
        "TblUsers",
        foreign_keys=[id_user],
        back_populates="reported_links",
        lazy="select",
    )

    finder = relationship(
        "TblUsers",
        foreign_keys=[id_finder],
        back_populates="found_links",
        lazy="select",
    )

    def __repr__(self):
        return f"<Report {self.id}>"

    def to_dict(self):
        return {"id": self.id, "id_meldung": self.id_meldung, "id_user": self.id_user}
