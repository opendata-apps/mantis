from sqlalchemy import text
from sqlalchemy.orm import Session
from flask import current_app

# Initial data for beschreibung table
INITIAL_BESCHREIBUNG_DATA = [
    (1, 'Im Haus'),
    (2, 'Im Garten'),
    (3, 'Auf dem Balkon/auf der Terrasse'),
    (4, 'Am Fenster/an der Hauswand'),
    (5, 'Industriebrache'),
    (6, 'Im Wald'),
    (7, 'Wiese/Weide'),
    (8, 'Heidelandschaft'),
    (9, 'Straßengraben/Wegesrand/Ruderalflur'),
    (10, 'Gewerbegebiet'),
    (11, 'Im oder am Auto'),
    (99, 'Anderer Fundort')
]

# Initial data for TblFeedbackType - UPDATED
INITIAL_FEEDBACK_TYPE_DATA = [
    (1, "Auf einer Veranstaltung"),
    (2, "Flyer/ Folder des Projektes"),
    (3, "Presse"), 
    (4, "Fernsehbeitrag"),
    (5, "Internetrecherche"), 
    (6, "Social Media"),
    (7, "Freunde, Bekannte, Kollegen"),
    (8, "Andere")
]

def populate_beschreibung(session: Session):
    """Populates the beschreibung table with initial data."""
    current_app.logger.info("Populating beschreibung table...")
    count = 0
    # Use INITIAL_BESCHREIBUNG_DATA directly
    for id, beschreibung in INITIAL_BESCHREIBUNG_DATA:
        try:
            # Check if the record already exists
            existing = session.execute(
                text("SELECT id FROM beschreibung WHERE id = :id"),
                {"id": id}
            ).fetchone()
            
            if not existing:
                session.execute(
                    text(
                        "INSERT INTO beschreibung (id, beschreibung) VALUES (:id, :beschreibung)"
                    ),
                    {"id": id, "beschreibung": beschreibung},
                )
                current_app.logger.info(f"Inserted beschreibung: {id} - {beschreibung}")
                count += 1
            else:
                current_app.logger.debug(f"Beschreibung record with id {id} already exists.")
        except Exception as e:
            current_app.logger.error(f"Error inserting beschreibung record {id}: {e}")
            session.rollback() # Rollback on error for this specific record
            raise # Re-raise the exception to potentially halt the process if critical
    if count > 0:
        session.commit()
    current_app.logger.info(f"Beschreibung table population complete. Inserted {count} new records.")


def populate_feedback_types(session: Session):
    """Populates the feedback_types table with initial data."""
    current_app.logger.info("Populating feedback_types table...")
    count = 0
    for id, name in INITIAL_FEEDBACK_TYPE_DATA:
        try:
            # Check if the record already exists
            existing = session.execute(
                text("SELECT id FROM feedback_types WHERE id = :id OR name = :name"),
                {"id": id, "name": name}
            ).fetchone()
            
            if not existing:
                session.execute(
                    text(
                        "INSERT INTO feedback_types (id, name) VALUES (:id, :name)"
                    ),
                    {"id": id, "name": name},
                )
                current_app.logger.info(f"Inserted feedback_type: {id} - {name}")
                count += 1
            else:
                 current_app.logger.debug(f"Feedback type record with id {id} or name '{name}' already exists.")
        except Exception as e:
            current_app.logger.error(f"Error inserting feedback_type record {id}: {e}")
            session.rollback() # Rollback on error
            raise # Re-raise
    if count > 0:
        session.commit()
    current_app.logger.info(f"Feedback_types table population complete. Inserted {count} new records.")


def populate_all(db_engine, session: Session, vg5000_json_data):
    """Populates all required tables with initial data."""
    current_app.logger.info("Starting initial data population...")
    
    populate_beschreibung(session)
    populate_feedback_types(session)
    
    # Import vg5000 data population function here
    # We need to ensure the vg5000 module and its function are accessible
    try:
        from .vg5000_fill_aemter import import_aemter_data
        current_app.logger.info("Populating VG5000 Aemter data...")
        import_aemter_data(db_engine, vg5000_json_data)
        current_app.logger.info("VG5000 Aemter data population complete.")
    except ImportError:
        current_app.logger.error("Could not import vg5000_fill_aemter. Skipping VG5000 data population.")
    except Exception as e:
        current_app.logger.error(f"Error during VG5000 data population: {e}")
        # Decide if you want to rollback or continue
        # session.rollback()
    
    current_app.logger.info("Initial data population finished.") 
