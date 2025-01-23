from sqlalchemy import text


def test_table_user(session):
    # Beispiel-Test, um zu prüfen, ob eine Tabelle existiert
    sql = """
    SELECT user_name, user_kontakt FROM users
    WHERE user_name like 'Oderwald%'
    """
    #WHERE user_id ='57e859de75710b51e2221804658c85574bc50a0c'
    result = session.execute(text(sql)).fetchall()
    print(60 * '#')
    print(result, type(result))
    print(60 * '+')
    #assert 'Oderwald E.' in result
    #assert 'damiangorlitz@example.com' in result
