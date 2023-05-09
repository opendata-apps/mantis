from app import db
from ..database import Base
from sqlalchemy import ForeignKey

class TblMeldungUser(db.Model):
    __tablename__ = "melduser"
    
    id = db.Column(db.Integer, primary_key=True)
    id_meldung = db.Column(db.Integer, db.ForeignKey("meldungen.id"), unique=False, nullable=False)
    id_user = db.Column(db.Integer, db.ForeignKey("users.id"), unique=False, nullable=False)

    def __repr__(self):
        return f'<Report {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'id_meldung': self.id_meldung,
            'id_user': self.id_user
        }
