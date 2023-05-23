from app import db
from database import Base

class TBLFundortbeschreibung(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    beschreibung = db.Column(db.varchar, nullable=False)

    def __repr__(self):
        return f'<Report {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'beschreibung': self.latbeschreibungitude
        }


