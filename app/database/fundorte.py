from sqlalchemy import Index

from app import db


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

    # Define index with PostgreSQL-specific operator class for pattern matching
    # Per SQLAlchemy docs: https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#operator-classes
    __table_args__ = (
        # Index for PREFIX LIKE queries: amt LIKE '12%', amt LIKE '120%', etc.
        # varchar_pattern_ops enables efficient pattern matching for LIKE 'prefix%'
        Index(
            "ix_fundorte_amt_pattern",
            "amt",
            postgresql_ops={"amt": "varchar_pattern_ops"},
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    plz = db.Column(db.Integer, nullable=False)
    ort = db.Column(db.String, nullable=False)
    strasse = db.Column(db.String(100), nullable=False)
    kreis = db.Column(db.String, nullable=False)
    land = db.Column(db.String(50), nullable=False)
    # amt (AGS code) - used in 8+ queries with LIKE 'prefix%' pattern
    amt = db.Column(db.String(50), nullable=True)
    mtb = db.Column(db.String(50), nullable=True)
    beschreibung = db.Column(
        db.Integer, db.ForeignKey("beschreibung.id"), nullable=False
    )
    longitude = db.Column(db.VARCHAR(25), nullable=False)
    latitude = db.Column(db.VARCHAR(25), nullable=False)
    ablage = db.Column(db.VARCHAR(255), nullable=False)

    def __repr__(self):
        return f"<Report {self.id}>"

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
