from app import db
from ..database import Base


class TblFundortBeschreibung(db.Model):
    __tablename__ = "beschreibung"

    id = db.Column(db.Integer, primary_key=True)
    beschreibung = db.Column(db.String(45), nullable=False)

    def __repr__(self):
        return f"<Report {self.id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "beschreibung": self.beschreibung,
        }
