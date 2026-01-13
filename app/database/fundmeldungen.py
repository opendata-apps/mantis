from sqlalchemy import Enum as SAEnum, Index

from app import db
from app.database.report_status import ReportStatus


class TblMeldungen(db.Model):
    """Sighting reports (Meldungen) model.

    Indexes:
        - ix_meldungen_status: Single column index on status (already exists from migration)
        - ix_meldungen_status_dat_fund_von: Composite index for filtered date range queries.
          Query patterns: WHERE status = ? AND dat_fund_von BETWEEN ? AND ?
        - ix_meldungen_dat_fund_von: Single column index for date-only queries.
          Query patterns: WHERE dat_fund_von >= ? (statistics, map filtering)
        - ix_meldungen_dat_meld: Index for meldedatum statistics queries.
        - ix_meldungen_fo_zuordnung: FK index for JOIN with fundorte table.

    Note: PostgreSQL does NOT auto-create indexes on foreign keys.
    """

    __tablename__ = "meldungen"

    # Define composite and additional indexes via __table_args__
    # Per SQLAlchemy docs: https://docs.sqlalchemy.org/en/20/orm/declarative_tables.html
    __table_args__ = (
        # Composite index: status + dat_fund_von for filtered date queries
        # Covers: WHERE status = 'APPR' AND dat_fund_von BETWEEN x AND y
        # Column order matters: status first (equality), then dat_fund_von (range)
        Index("ix_meldungen_status_dat_fund_von", "status", "dat_fund_von"),
        # Single column index for date-only queries (statistics without status filter)
        Index("ix_meldungen_dat_fund_von", "dat_fund_von"),
        # Index on dat_meld for statistics queries (7 queries use this)
        Index("ix_meldungen_dat_meld", "dat_meld"),
        # FK index for JOIN operations: meldungen.fo_zuordnung -> fundorte.id
        Index("ix_meldungen_fo_zuordnung", "fo_zuordnung"),
    )

    id = db.Column(db.Integer, primary_key=True)
    deleted = db.Column(db.Boolean, nullable=True)  # Deprecated: use status instead
    # Note: status already has index=True which creates ix_meldungen_status
    # We keep it for backward compatibility with existing migration
    status = db.Column(
        SAEnum(ReportStatus, native_enum=False, length=5),
        nullable=False,
        default=ReportStatus.OPEN,
        index=True,
    )
    dat_fund_von = db.Column(db.Date, nullable=False)
    dat_fund_bis = db.Column(db.Date, nullable=True)
    dat_meld = db.Column(db.Date, nullable=True)
    dat_bear = db.Column(db.Date, nullable=True)  # Keep for approval date tracking
    bearb_id = db.Column(db.String(40), nullable=True)
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

    def __repr__(self):
        return f"<Report {self.id}>"

    def to_dict(self):
        data = {
            "id": self.id,
            "deleted": self.deleted,
            "status": self.status,
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
        """Check if report is deleted (for backward compatibility)."""
        return self.status == ReportStatus.DEL

    @property
    def is_approved(self) -> bool:
        """Check if report is approved."""
        return self.status == ReportStatus.APPR

    @property
    def is_open(self) -> bool:
        """Check if report is open/pending."""
        return self.status == ReportStatus.OPEN

    @property
    def is_unclear(self) -> bool:
        """Check if report is marked as unclear."""
        return self.status == ReportStatus.UNKL

    @property
    def needs_info(self) -> bool:
        """Check if reporter was contacted for more info."""
        return self.status == ReportStatus.INFO
