"""
Diese Tabelle wird genutzt, um aus den
Koordinaten ein Amt zuzuordnen.
"""

from app import db
from sqlalchemy.dialects.postgresql import JSONB

class TblAemterCoordinaten(db.Model):
    __tablename__ = "aemter"

    ags = db.Column(db.Integer, primary_key=True)
    gen = db.Column(db.String(100), nullable=False)
    properties = db.Column(JSONB, nullable=False)

    def __repr__(self):
        return f"<Report {self.ags}>"

    def to_dict(self):
        return {
            "ags": self.ags,
            "gen": self.gen,
            "properties": self.properties,
        }
