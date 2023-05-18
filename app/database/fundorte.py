from ..database import Base
from app import db


class TblFundorte (db.Model):
    __tablename__ = "fundorte"

    id = db.Column(db.Integer, primary_key=True)
    plz = db.Column(db.Integer, nullable=False)
    ort = db.Column(db.String, nullable=False)
    strasse = db.Column(db.String(100), nullable=False)
    kreis = db.Column(db.String, nullable=False)
    land = db.Column(db.String(50), nullable=False)
    amt = db.Column(db.String(50), nullable=False)
    mtb = db.Column(db.String(50), nullable=False)
    beschreibung = db.Column(db.Integer, db.ForeignKey(
        "beschreibung.id"), nullable=False)
    longitude = db.Column(db.VARCHAR(25), nullable=False)
    latitude = db.Column(db.VARCHAR(25), nullable=False)
    beschreibung = db.Column(db.Integer, db.ForeignKey(
        "beschreibung.id"), nullable=False)
    ablage = db.Column(db.VARCHAR(255), nullable=False)

    def __repr__(self):
        return f'<Report {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'plz': self.plz,
            'ort': self.ort,
            'strasse': self.strasse,
            'kreis': self.kreis,
            'land': self.land,
            'amt': self.amt,
            'mtb': self.mtb,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'beschreibung': self.beschreibung,
            'ablage': self.ablage,
        }
