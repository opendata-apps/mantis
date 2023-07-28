from app import db
from ..database import Base


class TblMeldungen(db.Model):
    __tablename__ = "meldungen"

    id = db.Column(db.Integer, primary_key=True)
    deleted = db.Column(db.Boolean, nullable=True)
    dat_fund_von = db.Column(db.Date, nullable=False)
    dat_fund_bis = db.Column(db.Date, nullable=True)
    dat_meld = db.Column(db.Date, nullable=True)
    dat_bear = db.Column(db.Date, nullable=True)
    bearb_id = db.Column(db.String(40), nullable=True)
    tiere = db.Column(db.Integer, nullable=True)
    art_m = db.Column(db.Integer, nullable=True)
    art_w = db.Column(db.Integer, nullable=True)
    art_n = db.Column(db.Integer, nullable=True)
    art_o = db.Column(db.Integer, nullable=True)
    art_f = db.Column(db.Integer, nullable=True)

    fo_zuordnung = db.Column(
        db.Integer,  db.ForeignKey("fundorte.id"), nullable=True)
    fo_quelle = db.Column(db.String(1), nullable=True)
    fo_beleg = db.Column(db.String(1), nullable=True)
    anm_melder = db.Column(db.String(500), nullable=True)
    anm_bearbeiter = db.Column(db.String(500), nullable=True)

    def __repr__(self):
        return f'<Report {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'deleted': self.deleted,
            'dat_fund_von': self.dat_fund,
            'dat_fund_bis': self.dat_fund,
            'dat_meld': self.dat_meld,
            'dat_bear': self.dat_bear,
            'bearb_id': self.bearb_id,
            'tiere': self.tiere,
            'art_m': self.art_m,
            'art_w': self.art_w,
            'art_n': self.art_n,
            'art_o': self.art_o,
            'art_f': self.art_f,
            'fo_zuordung': self.fo_zuordnung,
            'fo_quelle': self.fo_quelle,
            'fo_beleg': self.fo_beleg,
            'anm_melder': self.anmerkung,
            'anm_bearbeiter': self.anmerkung,
        }
