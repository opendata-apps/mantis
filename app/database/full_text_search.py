from app import db
from sqlalchemy import text


class FullTextSearch:

    @staticmethod
    def create_materialized_view():
        print("Creating materialized view...")
        """
        Create the materialized view if it doesn't exist.
        This function can be called during app initialization.
        """
        db.session.execute(
            text(
                """
            CREATE MATERIALIZED VIEW IF NOT EXISTS full_text_search AS
            SELECT 
                m.id as meldungen_id,
                to_tsvector('german',
                    COALESCE(m.bearb_id, '') || ' ' ||
                    COALESCE(m.anm_melder, '') || ' ' ||
                    COALESCE(m.anm_bearbeiter, '') || ' ' ||
                    COALESCE(f.ort, '') || ' ' ||
                    COALESCE(f.strasse, '') || ' ' ||
                    COALESCE(f.kreis, '') || ' ' ||
                    COALESCE(f.land, '') || ' ' ||
                    COALESCE(f.amt, '') || ' ' ||
                    COALESCE(f.plz::text, '') || ' ' ||
                    COALESCE(f.mtb, '') || ' ' ||
                    COALESCE(b.beschreibung, '') || ' ' ||
                    COALESCE(mu.id_user::text, '') || ' ' ||
                    COALESCE(mu.id_finder::text, '') || ' ' ||
                    COALESCE(u.user_id, '') || ' ' ||
                    COALESCE(u.user_name, '') || ' ' ||
                    COALESCE(u.user_kontakt, '')
                ) as doc
            FROM 
                meldungen m
            LEFT JOIN 
                fundorte f ON m.fo_zuordnung = f.id
            LEFT JOIN 
                beschreibung b ON f.beschreibung = b.id
            LEFT JOIN 
                melduser mu ON m.id = mu.id_meldung
            LEFT JOIN 
                users u ON mu.id_user = u.id;
        """
            )
        )

        # Create an index for faster search
        db.session.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_full_text_search ON full_text_search USING gin(doc);
        """
            )
        )

        db.session.commit()

    @staticmethod
    def refresh_materialized_view():
        """
        Refresh the materialized view.
        This function can be called after significant data changes.
        """
        db.session.execute(text("REFRESH MATERIALIZED VIEW full_text_search;"))
        db.session.commit()
