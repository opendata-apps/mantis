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
    beschreibung = db.Column(db.String(45))
    melder_name = db.Column(db.String(45))
    melder_id = db.Column(db.String(40))
    melder_kontakt = db.Column(db.String(45))
    finder_name = db.Column(db.String(45))
    finder_id = db.Column(db.String(40))
    finder_kontakt = db.Column(db.String(45))

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
                    b.beschreibung,
                    u_melder.user_name AS melder_name,
                    u_melder.user_id AS melder_id,
                    u_melder.user_kontakt AS melder_kontakt,
                    u_finder.user_name AS finder_name,
                    u_finder.user_id AS finder_id,
                    u_finder.user_kontakt AS finder_kontakt
                FROM 
                    meldungen m
                LEFT JOIN 
                    fundorte f ON m.fo_zuordnung = f.id
                LEFT JOIN 
                    beschreibung b ON f.beschreibung = b.id
                LEFT JOIN 
                    melduser mu_melder ON m.id = mu_melder.id_meldung AND mu_melder.id_user = mu_melder.id_finder
                LEFT JOIN 
                    users u_melder ON mu_melder.id_user = u_melder.id
                LEFT JOIN 
                    melduser mu_finder ON m.id = mu_finder.id_meldung AND mu_finder.id_finder != mu_finder.id_user
                LEFT JOIN 
                    users u_finder ON mu_finder.id_finder = u_finder.id;
                """
            )
        )
        db.session.commit()

    @staticmethod
    def refresh_materialized_view():
        db.session.execute(text("REFRESH MATERIALIZED VIEW all_data_view;"))
        db.session.commit()