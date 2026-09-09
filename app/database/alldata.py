"""Read model for the admin spreadsheet view.

``all_data_view`` is a plain SQL view flattening meldungen + fundorte +
beschreibung + melduser + users. The view itself is created and managed
by Alembic migrations (see a4d8f2b6c573); this mapping lives on a
separate declarative base so Alembic autogenerate does not try to
manage it as a table.
"""

from datetime import date

from sqlalchemy import Date, Double, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class ViewBase(DeclarativeBase):
    """Separate base — keeps the view out of Alembic's metadata."""


class TblAllData(ViewBase):
    __tablename__ = "all_data_view"
    __table_args__ = {"schema": "public"}

    meldungen_id: Mapped[int] = mapped_column(primary_key=True)
    statuses: Mapped[list[str] | None] = mapped_column(ARRAY(String(5)))
    dat_fund_von: Mapped[date | None] = mapped_column(Date)
    dat_fund_bis: Mapped[date | None] = mapped_column(Date)
    dat_meld: Mapped[date | None] = mapped_column(Date)
    dat_bear: Mapped[date | None] = mapped_column(Date)
    bearb_id: Mapped[str | None] = mapped_column(String(40))
    tiere: Mapped[int | None]
    art_m: Mapped[int | None]
    art_w: Mapped[int | None]
    art_n: Mapped[int | None]
    art_o: Mapped[int | None]
    art_f: Mapped[int | None]
    fo_zuordnung: Mapped[int | None]
    fo_quelle: Mapped[str | None] = mapped_column(String(1))
    fo_beleg: Mapped[str | None] = mapped_column(String(1))
    anm_melder: Mapped[str | None] = mapped_column(String(500))
    anm_bearbeiter: Mapped[str | None] = mapped_column(String(500))
    fundorte_id: Mapped[int | None]
    plz: Mapped[str | None] = mapped_column(String(5))
    ort: Mapped[str | None]
    strasse: Mapped[str | None] = mapped_column(String(100))
    kreis: Mapped[str | None]
    land: Mapped[str | None] = mapped_column(String(50))
    amt: Mapped[str | None] = mapped_column(String(50))
    mtb: Mapped[str | None] = mapped_column(String(50))
    longitude: Mapped[float | None] = mapped_column(Double)
    latitude: Mapped[float | None] = mapped_column(Double)
    ablage: Mapped[str | None] = mapped_column(String(255))
    beschreibung_id: Mapped[int | None]
    beschreibung: Mapped[str | None] = mapped_column(String(45))
    # The view also exposes id_meldung and user_tbl_id; they are
    # intentionally unmapped so the admin grid (which derives its columns
    # from this model) never exposes them.
    id_user: Mapped[int | None]
    id_finder: Mapped[int | None]
    user_id: Mapped[str | None] = mapped_column(String(40))
    user_name: Mapped[str | None] = mapped_column(String(100))
    user_kontakt: Mapped[str | None] = mapped_column(String(254))
