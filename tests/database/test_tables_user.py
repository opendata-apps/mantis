from sqlalchemy import text


def test_table_user(session):
    sql = """
    SELECT user_name, user_kontakt FROM users
    WHERE user_name like 'Losekann%'
    """
    result = session.execute(text(sql)).fetchall()
    assert 'Losekann Z.' in result[0]

def test_table_user(session):
    sql = """
    SELECT user_name, user_kontakt FROM users
    WHERE user_kontakt like '%com'
    """
    result = session.execute(text(sql)).fetchall()
    assert len(result) == 7
