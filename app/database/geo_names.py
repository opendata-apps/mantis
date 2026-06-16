from sqlalchemy import BigInteger, Double, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app import db


class TblGeoNames(db.Model):
    """BKG GN250 populated places, used for Ortsteil-level coordinate grading."""

    __tablename__ = "geo_names"
    __table_args__ = (Index("ix_geo_names_name_norm", "name_norm"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text)
    name_norm: Mapped[str] = mapped_column(Text)
    ags: Mapped[int | None] = mapped_column(BigInteger)
    kreis: Mapped[str | None] = mapped_column(String(100))
    longitude: Mapped[float] = mapped_column(Double)
    latitude: Mapped[float] = mapped_column(Double)
