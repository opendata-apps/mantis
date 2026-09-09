from sqlalchemy import and_, not_
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.database.report_status import ReportStatus

if TYPE_CHECKING:
    from app.database.fundorte import TblFundorte
    from app.database.meldung_user import TblMeldungUser
    from app.database.users import TblUsers


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
        # DB-level mirror of ReportStatus.validate_combination(): the six
        # legal arrays are {OPEN}(+INFO/UNKL flags), {APPR}, {DEL}.
        CheckConstraint(
            "statuses = '{APPR}'::varchar[] "
            "OR statuses = '{DEL}'::varchar[] "
            "OR ('OPEN' = ANY(statuses) AND statuses <@ '{OPEN,INFO,UNKL}'::varchar[])",
            name="statuses_valid",
        ),
    )

    id: Mapped[int] = mapped_column(Identity(), primary_key=True)

    # Multi-select statuses array
    # Valid combinations enforced by ReportStatus.validate_combination()
    statuses: Mapped[list[str]] = mapped_column(
        ARRAY(String(5)),
        # Callable, not a literal list: a scalar mutable default is one shared
        # object across all instances, so an in-place mutation would leak.
        default=lambda: [ReportStatus.OPEN.value],
        server_default="{OPEN}",
    )
    dat_fund_von: Mapped[date] = mapped_column(Date)
    dat_fund_bis: Mapped[date | None] = mapped_column(Date)
    dat_meld: Mapped[date | None] = mapped_column(Date)
    # Keep for approval date tracking
    dat_bear: Mapped[date | None] = mapped_column(Date)
    bearb_id: Mapped[str | None] = mapped_column(
        String(40), ForeignKey("users.user_id", ondelete="SET NULL")
    )
    tiere: Mapped[int | None]
    art_m: Mapped[int | None]
    art_w: Mapped[int | None]
    art_n: Mapped[int | None]
    art_o: Mapped[int | None]
    art_f: Mapped[int | None]

    # Note: fo_zuordnung FK does NOT get auto-indexed by PostgreSQL
    fo_zuordnung: Mapped[int | None] = mapped_column(ForeignKey("fundorte.id"))
    fo_quelle: Mapped[str | None] = mapped_column(String(1))
    fo_beleg: Mapped[str | None] = mapped_column(String(1))
    anm_melder: Mapped[str | None] = mapped_column(String(500))
    anm_bearbeiter: Mapped[str | None] = mapped_column(String(500))

    # Full-text search vector, maintained by PostgreSQL triggers across
    # meldungen, fundorte, beschreibung, melduser, and users tables.
    # Weighted: A=location, B=people, C=details, D=notes
    search_vector: Mapped[str | None] = mapped_column(TSVECTOR)

    # Audit timestamps: when the row was inserted / last modified via the
    # ORM (bearb_id records who; raw SQL bypasses onupdate).
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # --- Relationships ---
    # Many-to-one: each report links to one location
    fundort: Mapped["TblFundorte | None"] = relationship(
        foreign_keys=[fo_zuordnung],
        back_populates="meldungen",
        lazy="select",
    )

    # One-to-one: each report has one melduser link row
    reporter_link: Mapped["TblMeldungUser | None"] = relationship(
        back_populates="meldung",
        lazy="select",
    )

    # Many-to-one: approver (reviewer who last touched this report)
    # Safe now that users.user_id has a UNIQUE constraint.
    approver: Mapped["TblUsers | None"] = relationship(
        foreign_keys=[bearb_id],
        lazy="select",
    )

    def __repr__(self):
        return f"<Report {self.id}>"

    def to_dict(self):
        data = {
            "id": self.id,
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

    @hybrid_property
    def is_deleted(self) -> bool:
        """Check if report is deleted."""
        return ReportStatus.DEL.value in (self.statuses or [])

    @is_deleted.inplace.expression
    @classmethod
    def _is_deleted_expression(cls):
        return cls.statuses.contains([ReportStatus.DEL.value])

    @hybrid_property
    def is_approved(self) -> bool:
        """Check if report is approved."""
        return ReportStatus.APPR.value in (self.statuses or [])

    @is_approved.inplace.expression
    @classmethod
    def _is_approved_expression(cls):
        return cls.statuses.contains([ReportStatus.APPR.value])

    @hybrid_property
    def is_open(self) -> bool:
        """Check if report is open/pending."""
        return ReportStatus.OPEN.value in (self.statuses or [])

    @is_open.inplace.expression
    @classmethod
    def _is_open_expression(cls):
        return cls.statuses.contains([ReportStatus.OPEN.value])

    @hybrid_property
    def is_unclear(self) -> bool:
        """Check if report is marked as unclear."""
        return ReportStatus.UNKL.value in (self.statuses or [])

    @is_unclear.inplace.expression
    @classmethod
    def _is_unclear_expression(cls):
        return cls.statuses.contains([ReportStatus.UNKL.value])

    @hybrid_property
    def needs_info(self) -> bool:
        """Check if reporter was contacted for more info."""
        return ReportStatus.INFO.value in (self.statuses or [])

    @needs_info.inplace.expression
    @classmethod
    def _needs_info_expression(cls):
        return cls.statuses.contains([ReportStatus.INFO.value])

    @hybrid_property
    def is_pending(self) -> bool:
        """Open, with nothing outstanding — the reviewer's default queue."""
        return self.is_open and not self.needs_info and not self.is_unclear

    @is_pending.inplace.expression
    @classmethod
    def _is_pending_expression(cls):
        # Built on the column rather than on the three hybrids above: a type
        # checker reads those by their `-> bool` getters and cannot know that
        # class-level access yields a SQL element instead.
        return and_(
            cls.statuses.contains([ReportStatus.OPEN.value]),
            not_(cls.statuses.contains([ReportStatus.INFO.value])),
            not_(cls.statuses.contains([ReportStatus.UNKL.value])),
        )


# The reviewer's filter vocabulary (the statusInput URL value) mapped onto the
# predicates above. Because those are hybrids, the same name works as a WHERE
# clause and as a check on a loaded row — so the list query and the HTMX card
# refresh cannot drift into disagreeing about what "offen" means.
# "all" is deliberately absent: it applies no restriction at all.
STATUS_FILTERS = {
    "bearbeitet": "is_approved",
    "offen": "is_pending",
    "geloescht": "is_deleted",
    "informiert": "needs_info",
    "unklar": "is_unclear",
}
