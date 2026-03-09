from sqlalchemy.orm import relationship

from app import db


class TblFundortBeschreibung(db.Model):
    __tablename__ = "beschreibung"

    id = db.Column(db.Integer, primary_key=True)
    beschreibung = db.Column(db.String(45), nullable=False)

    fundorte = relationship(
        "TblFundorte",
        back_populates="location_type",
        lazy="select",
    )

    def __repr__(self):
        return f"<Beschreibung {self.id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "beschreibung": self.beschreibung,
        }
