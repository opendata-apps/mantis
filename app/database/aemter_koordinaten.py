"""
Diese Tabelle wird genutzt, um aus den
Koordinaten ein Amt zuzuordnen.
"""

from app import db
from sqlalchemy.dialects.postgresql import JSONB


class TblAemterCoordinaten(db.Model):
    __tablename__ = "aemter"

    # Natural key: official AGS code, always assigned explicitly
    ags = db.Column(db.Integer, primary_key=True, autoincrement=False)
    gen = db.Column(db.String(100), nullable=False)
    properties = db.Column(JSONB, nullable=False)

    def __repr__(self):
        return f"<Amt {self.ags}>"

    def to_dict(self):
        return {
            "ags": self.ags,
            "gen": self.gen,
            "properties": self.properties,
        }
