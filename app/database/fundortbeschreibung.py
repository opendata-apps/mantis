from typing import TYPE_CHECKING

from sqlalchemy import Identity, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from app.database.fundorte import TblFundorte


class TblFundortBeschreibung(db.Model):
    __tablename__ = "beschreibung"

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    beschreibung: Mapped[str] = mapped_column(String(45))

    fundorte: Mapped[list["TblFundorte"]] = relationship(
        back_populates="location_type",
        lazy="select",
    )

    def __repr__(self):
        return f"<Beschreibung {self.id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "beschreibung": self.beschreibung,
        }
