from app import db
from ..database import Base


class TblTiere (db.Model):
    id = db.Column(db.Integer, primary_key=True)
    art = db.Column(db.Integer, primary_key=True)

    def __repr__(self):
        return f'<Report {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'art': self.art,
        }
