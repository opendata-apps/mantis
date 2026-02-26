import sqlalchemy as sa
import sqlalchemy.schema
import sqlalchemy.orm as orm
from sqlalchemy import text, event
from sqlalchemy.ext import compiler
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from typing import Optional
from app import db

meta = sa.MetaData()
# Separate Base for the materialized view — intentionally decoupled from
# db.Model so Alembic does not try to manage this view as a regular table.
Base = orm.declarative_base()


class TblAllData(Base):
    __tablename__ = "all_data_view"
    __table_args__ = {"schema": "public"}

    meldungen_id = db.Column(db.Integer, primary_key=True)
    deleted = db.Column(db.Boolean)
    statuses = db.Column(db.ARRAY(db.String(5)))
    dat_fund_von = db.Column(db.Date)
    dat_fund_bis = db.Column(db.Date)
    dat_meld = db.Column(db.Date)
    dat_bear = db.Column(db.Date)
    bearb_id = db.Column(db.String(40))
    tiere = db.Column(db.Integer)
    art_m = db.Column(db.Integer)
    art_w = db.Column(db.Integer)
    art_n = db.Column(db.Integer)
    art_o = db.Column(db.Integer)
    art_f = db.Column(db.Integer)
    fo_quelle = db.Column(db.String(1))
    fo_beleg = db.Column(db.String(1))
    anm_melder = db.Column(db.String(500))
    anm_bearbeiter = db.Column(db.String(500))
    fundorte_id = db.Column(db.Integer)
    plz = db.Column(db.Integer)
    ort = db.Column(db.String)
    strasse = db.Column(db.String(100))
    kreis = db.Column(db.String)
    land = db.Column(db.String(50))
    amt = db.Column(db.String(50))
    mtb = db.Column(db.String(50))
    longitude = db.Column(db.String(25))
    latitude = db.Column(db.String(25))
    ablage = db.Column(db.String(255))
    beschreibung_id = db.Column(db.Integer)
    beschreibung = db.Column(db.String(45))
    id_user = db.Column(db.Integer)
    id_finder = db.Column(db.Integer)
    user_id = db.Column(db.Integer)
    user_name = db.Column(db.String(45))
    user_kontakt = db.Column(db.String(45))


class Create(sa.schema.DDLElement):
    def __init__(self, name, select, schema="public"):
        self.name = name
        self.schema = schema
        self.select = select

        event.listen(meta, "after_create", self)


@compiler.compiles(Create)
def createGen(element, compiler, **kwargs):
    return 'CREATE MATERIALIZED VIEW {schema}."{name}" AS {select}'.format(
        name=element.name,
        schema=element.schema,
        select=compiler.sql_compiler.process(element.select, literal_binds=True),
    )


def create_materialized_view(
    db: Optional[Engine] = None, session: Optional[Session] = None
) -> None:
    "create or recreate a materialized view for admin data"
    if not db:
        from flask import current_app

        db = sa.create_engine(current_app.config["SQLALCHEMY_DATABASE_URI"])

    if not session:
        SessionClass = orm.sessionmaker(bind=db)
        session = SessionClass()

    # Drop the existing materialized view if it exists
    try:
        session.execute(text('DROP MATERIALIZED VIEW IF EXISTS public."all_data_view"'))
        session.commit()
    except Exception:
        session.rollback()

    # Table Aliases
    meldungen = sa.table(
        "meldungen",
        sa.column("id"),
        sa.column("deleted"),
        sa.column("statuses"),
        sa.column("dat_fund_von"),
        sa.column("dat_fund_bis"),
        sa.column("dat_meld"),
        sa.column("dat_bear"),
        sa.column("bearb_id"),
        sa.column("tiere"),
        sa.column("art_m"),
        sa.column("art_w"),
        sa.column("art_n"),
        sa.column("art_o"),
        sa.column("art_f"),
        sa.column("fo_zuordnung"),
        sa.column("fo_quelle"),
        sa.column("fo_beleg"),
        sa.column("anm_melder"),
        sa.column("anm_bearbeiter"),
    )
    fundorte = sa.table(
        "fundorte",
        sa.column("id"),
        sa.column("plz"),
        sa.column("ort"),
        sa.column("strasse"),
        sa.column("kreis"),
        sa.column("land"),
        sa.column("amt"),
        sa.column("mtb"),
        sa.column("longitude"),
        sa.column("latitude"),
        sa.column("ablage"),
        sa.column("beschreibung"),
    )
    beschreibung = sa.table("beschreibung", sa.column("id"), sa.column("beschreibung"))
    melduser = sa.table(
        "melduser",
        sa.column("id"),
        sa.column("id_meldung"),
        sa.column("id_user"),
        sa.column("id_finder"),
    )
    users = sa.table(
        "users",
        sa.column("id"),
        sa.column("user_id"),
        sa.column("user_name"),
        sa.column("user_kontakt"),
    )

    # Query Definition
    view_query = sa.select(
        meldungen.c.id.label("meldungen_id"),
        meldungen.c.deleted,
        meldungen.c.statuses,
        meldungen.c.dat_fund_von,
        meldungen.c.dat_fund_bis,
        meldungen.c.dat_meld,
        meldungen.c.dat_bear,
        meldungen.c.bearb_id,
        meldungen.c.tiere,
        meldungen.c.art_m,
        meldungen.c.art_w,
        meldungen.c.art_n,
        meldungen.c.art_o,
        meldungen.c.art_f,
        meldungen.c.fo_zuordnung,
        meldungen.c.fo_quelle,
        meldungen.c.fo_beleg,
        meldungen.c.anm_melder,
        meldungen.c.anm_bearbeiter,
        fundorte.c.id.label("fundorte_id"),
        fundorte.c.plz,
        fundorte.c.ort,
        fundorte.c.strasse,
        fundorte.c.kreis,
        fundorte.c.land,
        fundorte.c.amt,
        fundorte.c.mtb,
        fundorte.c.longitude,
        fundorte.c.latitude,
        fundorte.c.ablage,
        beschreibung.c.id.label("beschreibung_id"),
        beschreibung.c.beschreibung,
        melduser.c.id_meldung,
        melduser.c.id_user,
        melduser.c.id_finder,
        users.c.id.label("user_tbl_id"),
        users.c.user_id,
        users.c.user_name,
        users.c.user_kontakt,
    ).select_from(
        meldungen.outerjoin(fundorte, meldungen.c.fo_zuordnung == fundorte.c.id)
        .outerjoin(beschreibung, fundorte.c.beschreibung == beschreibung.c.id)
        .outerjoin(melduser, meldungen.c.id == melduser.c.id_meldung)
        .outerjoin(users, melduser.c.id_user == users.c.id)
    )

    # Create View
    Create(name="all_data_view", select=view_query)
    meta.create_all(bind=db, checkfirst=True)
    session.commit()
    session.close()


def refresh_materialized_view(db):
    "Refresh the materialized view"
    db.session.execute(text("REFRESH MATERIALIZED VIEW all_data_view"))
    db.session.commit()


if __name__ == "__main__":
    create_materialized_view()
