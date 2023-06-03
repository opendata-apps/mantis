from app.tools.gen_user_id import get_new_id


def test_lengt_of_new_id():

    userid = get_new_id()
    assert len(userid) == 40
