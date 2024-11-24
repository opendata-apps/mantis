from app import db
from sqlalchemy import text

class TblAllData(db.Model):
    __tablename__ = 'all_data_view'

    id = db.Column(db.Integer, primary_key=True)
    deleted = db.Column(db.Boolean)
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
    fundorte_id = db.Column(db.Integer)  # New field
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
    beschreibung_id = db.Column(db.Integer)  # New field
    beschreibung = db.Column(db.String(45))
    report_user_db_id = db.Column(db.Integer)
    report_user_id = db.Column(db.String(40))
    report_user_name = db.Column(db.String(45))
    report_user_kontakt = db.Column(db.String(45))

    def __repr__(self):
        return f"<AllData {self.id}>"

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @staticmethod
    def create_materialized_view():
        print("Creating materialized view for all_data...")
        db.session.execute(
            text(
                """
                CREATE MATERIALIZED VIEW IF NOT EXISTS all_data_view AS
                SELECT 
                    m.id,
                    m.deleted,
                    m.dat_fund_von,
                    m.dat_fund_bis,
                    m.dat_meld,
                    m.dat_bear,
                    m.bearb_id,
                    m.tiere,
                    m.art_m,
                    m.art_w,
                    m.art_n,
                    m.art_o,
                    m.art_f,
                    m.fo_quelle,
                    m.fo_beleg,
                    m.anm_melder,
                    m.anm_bearbeiter,
                    f.id AS fundorte_id,  -- Include fundorte.id
                    f.plz,
                    f.ort,
                    f.strasse,
                    f.kreis,
                    f.land,
                    f.amt,
                    f.mtb,
                    f.longitude,
                    f.latitude,
                    f.ablage,
                    b.id AS beschreibung_id,  -- Include beschreibung.id
                    b.beschreibung,
                    report_user.id AS report_user_db_id,
                    report_user.user_id AS report_user_id,
                    report_user.user_name AS report_user_name,
                    report_user.user_kontakt AS report_user_kontakt
                FROM 
                    meldungen m
                LEFT JOIN 
                    fundorte f ON m.fo_zuordnung = f.id
                LEFT JOIN 
                    beschreibung b ON f.beschreibung = b.id
                LEFT JOIN LATERAL (
                    SELECT u.*
                    FROM melduser mu
                    JOIN users u ON mu.id_user = u.id
                    WHERE mu.id_meldung = m.id AND u.user_rolle IN ('1', '9')
                    LIMIT 1
                ) report_user ON TRUE;
                """
            )
        )
        db.session.commit()

    @staticmethod
    def refresh_materialized_view():
        db.session.execute(text("REFRESH MATERIALIZED VIEW all_data_view;"))
        db.session.commit()