from sqlalchemy import Index
from sqlalchemy.dialects.postgresql import ARRAY, TSVECTOR
from sqlalchemy.orm import relationship

from app import db
from app.database.report_status import ReportStatus


class TblMeldungen(db.Model):
    """Sighting reports (Meldungen) model.

    Indexes:
        - ix_meldungen_statuses_gin: GIN index on statuses array for containment queries
        - ix_meldungen_dat_fund_von: Single column index for date-only queries.
          Query patterns: WHERE dat_fund_von >= ? (statistics, map filtering)
        - ix_meldungen_dat_meld: Index for meldedatum statistics queries.
        - ix_meldungen_fo_zuordnung: FK index for JOIN with fundorte table.

    Note: PostgreSQL does NOT auto-create indexes on foreign keys.
    Note: GIN indexes don't combine well in composite indexes with B-tree.
          PostgreSQL query planner will use bitmap index scan to combine them.
    """

    __tablename__ = "meldungen"

    # Define indexes via __table_args__
    # Per SQLAlchemy docs: https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html
    __table_args__ = (
        # GIN index for array containment queries: statuses @> '{APPR}'
        Index("ix_meldungen_statuses_gin", "statuses", postgresql_using="gin"),
        # Single column index for date-only queries (statistics without status filter)
        Index("ix_meldungen_dat_fund_von", "dat_fund_von"),
        # Index on dat_meld for statistics queries (7 queries use this)
        Index("ix_meldungen_dat_meld", "dat_meld"),
        # FK index for JOIN operations: meldungen.fo_zuordnung -> fundorte.id
        Index("ix_meldungen_fo_zuordnung", "fo_zuordnung"),
        # GIN index for full-text search via tsvector column
        # fastupdate=off: each write updates GIN immediately (slightly slower writes)
        # but reads never scan a pending list (consistently fast reads, no latency spikes)
        Index(
            "ix_meldungen_search_vector_gin",
            "search_vector",
            postgresql_using="gin",
            postgresql_with={"fastupdate": "off"},
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    deleted = db.Column(db.Boolean, nullable=True)  # Deprecated: use statuses instead

    # Multi-select statuses array
    # Valid combinations enforced by ReportStatus.validate_combination()
    statuses = db.Column(
        ARRAY(db.String(5)),
        nullable=False,
        default=[ReportStatus.OPEN.value],
        server_default="{OPEN}",
    )
    dat_fund_von = db.Column(db.Date, nullable=False)
    dat_fund_bis = db.Column(db.Date, nullable=True)
    dat_meld = db.Column(db.Date, nullable=True)
    dat_bear = db.Column(db.Date, nullable=True)  # Keep for approval date tracking
    bearb_id = db.Column(db.String(40), db.ForeignKey("users.user_id"), nullable=True)
    tiere = db.Column(db.Integer, nullable=True)
    art_m = db.Column(db.Integer, nullable=True)
    art_w = db.Column(db.Integer, nullable=True)
    art_n = db.Column(db.Integer, nullable=True)
    art_o = db.Column(db.Integer, nullable=True)
    art_f = db.Column(db.Integer, nullable=True)

    # Note: fo_zuordnung FK does NOT get auto-indexed by PostgreSQL
    fo_zuordnung = db.Column(db.Integer, db.ForeignKey("fundorte.id"), nullable=True)
    fo_quelle = db.Column(db.String(1), nullable=True)
    fo_beleg = db.Column(db.String(1), nullable=True)
    anm_melder = db.Column(db.String(500), nullable=True)
    anm_bearbeiter = db.Column(db.String(500), nullable=True)

    # Full-text search vector, maintained by PostgreSQL triggers across
    # meldungen, fundorte, beschreibung, melduser, and users tables.
    # Weighted: A=location, B=people, C=details, D=notes
    search_vector = db.Column(TSVECTOR)

    # --- Relationships ---
    # Many-to-one: each report links to one location
    fundort = relationship(
        "TblFundorte",
        foreign_keys=[fo_zuordnung],
        back_populates="meldungen",
        lazy="select",
    )

    # One-to-one: each report has one melduser link row
    reporter_link = relationship(
        "TblMeldungUser",
        back_populates="meldung",
        uselist=False,
        lazy="select",
    )

    # Many-to-one: approver (reviewer who last touched this report)
    # Safe now that users.user_id has a UNIQUE constraint.
    approver = relationship(
        "TblUsers",
        foreign_keys=[bearb_id],
        uselist=False,
        lazy="select",
    )

    def __repr__(self):
        return f"<Report {self.id}>"

    def to_dict(self):
        data = {
            "id": self.id,
            "deleted": self.deleted,
            "statuses": self.statuses,
            "dat_fund_von": self.dat_fund_von,
            "dat_fund_bis": self.dat_fund_bis,
            "dat_meld": self.dat_meld,
            "dat_bear": self.dat_bear,
            "bearb_id": self.bearb_id,
            "tiere": self.tiere,
            "art_m": self.art_m,
            "art_w": self.art_w,
            "art_n": self.art_n,
            "art_o": self.art_o,
            "art_f": self.art_f,
            "fo_zuordnung": self.fo_zuordnung,
            "fo_quelle": self.fo_quelle,
            "fo_beleg": self.fo_beleg,
            "anm_melder": self.anm_melder,
            "anm_bearbeiter": self.anm_bearbeiter,
        }
        return data

    @property
    def is_deleted(self) -> bool:
        """Check if report is deleted."""
        return ReportStatus.DEL.value in (self.statuses or [])

    @property
    def is_approved(self) -> bool:
        """Check if report is approved."""
        return ReportStatus.APPR.value in (self.statuses or [])

    @property
    def is_open(self) -> bool:
        """Check if report is open/pending."""
        return ReportStatus.OPEN.value in (self.statuses or [])

    @property
    def is_unclear(self) -> bool:
        """Check if report is marked as unclear."""
        return ReportStatus.UNKL.value in (self.statuses or [])

    @property
    def needs_info(self) -> bool:
        """Check if reporter was contacted for more info."""
        return ReportStatus.INFO.value in (self.statuses or [])
