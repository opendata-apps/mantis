from app.tools.mtb_calc import get_mtb


def test_get_mtb_for_trebbin(session):

    point = [13.440228, 51.738052]
    mtb = get_mtb(point[1], point[0])

    assert mtb == "4246"
