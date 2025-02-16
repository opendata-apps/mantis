from sqlalchemy import text


def test_table_beschreibung__exists(session):
    # Beispiel-Test, um zu prüfen, ob eine Tabelle existiert
    result = session.execute(text("SELECT * FROM beschreibung")).fetchall()
    assert len(result) == 12
