from sqlalchemy import Enum as SAEnum

from app import db
from app.database.report_status import ReportStatus


class TblMeldungen(db.Model):
    __tablename__ = "meldungen"

    id = db.Column(db.Integer, primary_key=True)
    deleted = db.Column(db.Boolean, nullable=True)  # Deprecated: use status instead
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
