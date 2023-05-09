from app import db
from alembic import op
from ..database import Base

class TblPlzOrt(db.Model):
    __tablename__ = "plzort"
    
    osm_id = db.Column(db.Integer, primary_key=True)
    ags = db.Column(db.Integer, nullable=True)
    ort = db.Column(db.String(100), nullable=False)
    plz = db.Column(db.Integer, nullable=False)
    landkreis = db.Column(db.String(100), nullable=True)
    bundesland = db.Column(db.String(45), nullable=True)

    def __repr__(self):
        return f'<Report {self.osm_id}>'

    def to_dict(self):
        return {
            'osm_id': self.osm_id,
            'ags': self.ags,
            'ort': self.ort,
            'plz': self.plz,
            'landkreis': self.landkreis,
            'bundesland': self.bundesland
        }

# op.create_primary_key("pk_tbl_plz_ort", "TblPlzOrt", ["osm_id", "plz"])
