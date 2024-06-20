"""
Diese Tabelle wird genutzt, um aus den
Koordinaten ein Amt zuzuordnen.
"""

from app import db
from geoalchemy2 import Geometry

class TblAemterCoordinaten(db.Model):
    __tablename__ = "aemter"

    ags = db.Column(db.String, primary_key=True)
    gen = db.Column(db.String(100), nullable=False)
    geom = db.Column(Geometry("GEOMETRYZ", srid=4326), nullable=False)

    def __repr__(self):
        return f"<Amt {self.ags}>"

    def to_dict(self):
        return {
            "ags": self.ags,
            "gen": self.gen,
        }
