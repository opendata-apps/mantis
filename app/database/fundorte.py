from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Double,
    ForeignKey,
    Identity,
    Index,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from app.database.fundmeldungen import TblMeldungen
    from app.database.fundortbeschreibung import TblFundortBeschreibung


class TblFundorte(db.Model):
    """Location data (Fundorte) for sighting reports.

    Indexes:
        - ix_fundorte_amt_pattern: B-tree index with varchar_pattern_ops for prefix LIKE queries.
          Query patterns: WHERE amt LIKE '12%' (AGS code filtering)
          Per PostgreSQL docs: https://www.postgresql.org/docs/current/indexes-opclass.html
          varchar_pattern_ops enables index usage for LIKE 'prefix%' patterns in non-C locales.

    Note: Standard B-tree indexes cannot optimize LIKE queries in non-C locales without
    using the appropriate operator class (varchar_pattern_ops or text_pattern_ops).
    """

    __tablename__ = "fundorte"

    __table_args__ = (
        # Index for PREFIX LIKE queries: amt LIKE '12%', amt LIKE '120%', etc.
        # varchar_pattern_ops enables efficient pattern matching for LIKE 'prefix%'
        Index(
            "ix_fundorte_amt_pattern",
            "amt",
            postgresql_ops={"amt": "varchar_pattern_ops"},
        ),
        # German PLZ are 5-digit identifiers with significant leading zeros
        # (01067 Dresden) — never store as integer.
        CheckConstraint("plz ~ '^[0-9]{5}$'", name="plz_format"),
        CheckConstraint("latitude BETWEEN -90 AND 90", name="latitude_range"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="longitude_range"),
    )

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)
    # NULL = reporter gave no PLZ (the form field is optional)
    plz: Mapped[str | None] = mapped_column(String(5))
    ort: Mapped[str]
    strasse: Mapped[str] = mapped_column(String(100))
    kreis: Mapped[str]
    land: Mapped[str] = mapped_column(String(50))
    # amt (AGS code) - used in 8+ queries with LIKE 'prefix%' pattern
    amt: Mapped[str | None] = mapped_column(String(50))
    mtb: Mapped[str | None] = mapped_column(String(50))
    beschreibung: Mapped[int] = mapped_column(ForeignKey("beschreibung.id"))
    longitude: Mapped[float] = mapped_column(Double)
    latitude: Mapped[float] = mapped_column(Double)
    ablage: Mapped[str] = mapped_column(String(255))

    # Audit timestamps: when the row was inserted / last modified via the
    # ORM (bearb_id records who; raw SQL bypasses onupdate).
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # --- Relationships ---
    meldungen: Mapped[list["TblMeldungen"]] = relationship(
        back_populates="fundort",
        lazy="select",
    )

    # Named `location_type` to avoid collision with the `beschreibung` FK column
    location_type: Mapped["TblFundortBeschreibung"] = relationship(
        foreign_keys=[beschreibung],
        back_populates="fundorte",
        lazy="select",
    )

    def __repr__(self):
        return f"<Fundort {self.id}>"

    def to_dict(self):
        return {
            "id": self.id,
            "plz": self.plz,
            "ort": self.ort,
            "strasse": self.strasse,
            "kreis": self.kreis,
            "land": self.land,
            "amt": self.amt,
            "mtb": self.mtb,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "beschreibung": self.beschreibung,
            "ablage": self.ablage,
        }
