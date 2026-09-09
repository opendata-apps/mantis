"""The map offset must not be averageable away."""

from statistics import mean

from app.routes.data import obfuscate_location

TRUE_LAT, TRUE_LON = 52.5200, 13.4050


def test_same_report_always_lands_on_the_same_point(app):
    with app.app_context():
        first = obfuscate_location(TRUE_LAT, TRUE_LON, 4711)
        again = [obfuscate_location(TRUE_LAT, TRUE_LON, 4711) for _ in range(50)]

    assert all(point == first for point in again)


def test_different_reports_get_different_offsets(app):
    with app.app_context():
        points = {obfuscate_location(TRUE_LAT, TRUE_LON, i) for i in range(50)}

    assert len(points) == 50


def test_repeated_views_do_not_converge_on_the_true_position(app):
    """The attack the per-request offset was open to.

    Averaging N independent draws shrinks the error by sqrt(N), so a few dozen
    page loads used to narrow a sighting to tens of metres. With one offset per
    report the mean stays put, wherever the offset happened to fall.
    """
    with app.app_context():
        views = [obfuscate_location(TRUE_LAT, TRUE_LON, 4711) for _ in range(500)]

    lat_error = abs(mean(lat for lat, _ in views) - TRUE_LAT)
    lon_error = abs(mean(lon for _, lon in views) - TRUE_LON)

    # A converging estimator would put this near zero; a fixed offset cannot.
    assert lat_error == abs(views[0][0] - TRUE_LAT)
    assert lon_error == abs(views[0][1] - TRUE_LON)


def test_offset_stays_within_the_documented_bound(app):
    with app.app_context():
        points = [obfuscate_location(TRUE_LAT, TRUE_LON, i) for i in range(200)]

    assert all(abs(lat - TRUE_LAT) <= 0.005 for lat, _ in points)
    assert all(abs(lon - TRUE_LON) <= 0.005 for _, lon in points)
