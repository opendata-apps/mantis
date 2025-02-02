from sqlalchemy import text


def test_table_meldungen__exists(session):
    # Beispiel-Test, um zu prüfen, ob eine Tabelle existiert
    result = session.execute(text("SELECT * FROM meldungen")).fetchall()
    assert len(result) == 20

def test_table_meldungen__count(session):
    result = session.execute(text("SELECT count(*) FROM meldungen")).fetchone()
    assert result[0] == 20
