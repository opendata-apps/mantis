"""
Diese Tabelle wird genutzt, um aus den
Koordinaten ein Amt zuzuordnen.
"""

from typing import Any

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column


from app.extensions import db

class TblAemterCoordinaten(db.Model):
    __tablename__ = "aemter"

    # Natural key: official AGS code, always assigned explicitly
    ags: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    gen: Mapped[str] = mapped_column(String(100))
    # GeoJSON geometry of the municipality polygon
    properties: Mapped[dict[str, Any]] = mapped_column(JSONB)

    def __repr__(self):
        return f"<Amt {self.ags}>"

    def to_dict(self):
        return {
            "ags": self.ags,
            "gen": self.gen,
            "properties": self.properties,
        }
