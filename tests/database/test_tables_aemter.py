from sqlalchemy import text
from app.database.vg5000_fill_aemter import import_aemter_data
import psycopg2


def test_table_aemter_exists(session):
    # Beispiel-Test, um zu prüfen, ob eine Tabelle existiert
    from jsondata import data as testdata
    conn = psycopg2.connect(
        dbname="mantis_tester",
        user="mantis_user",
        password="mantis",
        host="localhost"
    )

    import_aemter_data(conn, testdata)

    result = session.execute(text("SELECT * FROM aemter")).fetchall()
    assert len(result) == 4
