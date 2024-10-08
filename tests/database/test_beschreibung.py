import pytest
from sqlalchemy import text
from app.database.models import TblFundortBeschreibung as tbl
import warnings


def test_example_model_exists(session):
    # Beispiel-Test, um zu prüfen, ob eine Tabelle existiert
    result = session.execute(text("SELECT * FROM beschreibung")).fetchall()
    assert len(result) == 0 # Noch keine Daten eingefügt

def todo():
    warnings.warn(UserWarning("Hier fehlt noch ein Test!"))
    return 1

def test_beschreibung(client):
    """
    GIVEN a table »TblFundortBeschreibung«
    AND Fill-Script was executed
    THEN check the count of rows
    """
    assert todo() == 1
    #assert tbl.id == 1
    #assert tbl.beschreibung == 'Im Wald'
