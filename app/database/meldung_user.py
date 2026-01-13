from sqlalchemy import Index

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
    # FK to meldungen - used in every JOIN operation
    id_meldung = db.Column(
        db.Integer, db.ForeignKey("meldungen.id"), unique=False, nullable=False
    )
    # FK to users - used in every JOIN operation
    id_user = db.Column(
        db.Integer, db.ForeignKey("users.id"), unique=False, nullable=False
    )
    # FK to finder (optional) - not frequently queried, no index needed
    id_finder = db.Column(
        db.Integer, db.ForeignKey("users.id"), unique=False, nullable=True
    )

    def __repr__(self):
        return f"<Report {self.id}>"

    def to_dict(self):
        return {"id": self.id, "id_meldung": self.id_meldung, "id_user": self.id_user}
