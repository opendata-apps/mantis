from app import db
from ..database import Base

class TblMeldungen(db.Model):
    __tablename__ = "meldungen"
    
    id = db.Column(db.Integer, primary_key=True)
    dat_fund = db.Column(db.Date, nullable=False)
    dat_meld = db.Column(db.Date, nullable=False)
    dat_bear = db.Column(db.Date, nullable=True)
    anzahl = db.Column(db.Integer, nullable=True)
    fo_zuordung = db.Column(db.Integer,  db.ForeignKey("fundorte.id"), nullable=True)
    fo_quelle = db.Column(db.String(1), nullable=False)
    fo_kategorie= db.Column(db.String(1), nullable=False)
    anmerkung = db.Column(db.String(500), nullable=True)
    
    def __repr__(self):
        return f'<Report {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'dat_fund': self.dat_fund,
            'dat_meld': self.dat_meld,
            'dat_bear': self.dat_bear,
            'anzahl': self.anzahl,
            'fo_zuordung': self.fo_zuordnung,
            'fo_quelle': self.fo_quelle,
            'fo_kategorie': self.fo_kategorie,
            'anmerkung': self.anmerkung,
        }
