from sqlalchemy.orm import Session
from flask import current_app

from app.database.fundortbeschreibung import TblFundortBeschreibung

# Initial data for beschreibung table
INITIAL_BESCHREIBUNG_DATA = [
    (1, "Im Haus"),
    (2, "Im Garten"),
    (3, "Auf dem Balkon/auf der Terrasse"),
    (4, "Am Fenster/an der Hauswand"),
    (5, "Industriebrache"),
    (6, "Im Wald"),
    (7, "Wiese/Weide"),
    (8, "Heidelandschaft"),
    (9, "Straßengraben/Wegesrand/Ruderalflur"),
    (10, "Gewerbegebiet"),
    (11, "Im oder am Auto"),
    (99, "Anderer Fundort"),
]


def populate_beschreibung(session: Session):
    """Populates the beschreibung table with initial data."""
    current_app.logger.info("Populating beschreibung table...")
    count = 0
    for id, beschreibung in INITIAL_BESCHREIBUNG_DATA:
        if not session.get(TblFundortBeschreibung, id):
            session.add(TblFundortBeschreibung(id=id, beschreibung=beschreibung))
            current_app.logger.info(f"Inserted beschreibung: {id} - {beschreibung}")
            count += 1
        else:
            current_app.logger.debug(
                f"Beschreibung record with id {id} already exists."
            )
    if count > 0:
        session.commit()
    current_app.logger.info(
        f"Beschreibung table population complete. Inserted {count} new records."
    )


def populate_all(db_engine, session: Session, vg5000_json_data):
    """Populates all required tables with initial data."""
    current_app.logger.info("Starting initial data population...")

    populate_beschreibung(session)

    if vg5000_json_data is None:
        current_app.logger.warning(
            "No VG5000 data provided. Skipping aemter population. "
            "Run 'flask seed-ags' to fetch administrative area data."
        )
    else:
        try:
            from .vg5000_fill_aemter import import_aemter_data

            current_app.logger.info("Populating VG5000 Aemter data...")
            import_aemter_data(session, vg5000_json_data)
            current_app.logger.info("VG5000 Aemter data population complete.")
        except ImportError:
            current_app.logger.error(
                "Could not import vg5000_fill_aemter. Skipping VG5000 data population."
            )
        except Exception as e:
            current_app.logger.error(f"Error during VG5000 data population: {e}")

    current_app.logger.info("Initial data population finished.")
