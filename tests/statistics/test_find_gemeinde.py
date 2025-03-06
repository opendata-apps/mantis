from app.tools.find_gemeinde import get_amt_full_scan


def test_amt_for_fichtwald(session):

    point = ['13.440228', '51.738052']
    amt = get_amt_full_scan(point)

    assert amt == "12062134 -- Fichtwald"
