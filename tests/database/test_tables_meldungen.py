from sqlalchemy import text


def test_table_meldungen__exists(session):
    # Beispiel-Test, um zu prüfen, ob eine Tabelle existiert
    result = session.execute(text("SELECT * FROM meldungen")).fetchall()
    assert len(result) == 50
