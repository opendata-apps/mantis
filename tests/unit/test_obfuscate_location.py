"""The map offset must not be averageable away."""

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


def test_secret_key_changes_the_report_offset(app):
    with app.app_context():
        app.config["SECRET_KEY"] = "first-map-test-secret"
        first = obfuscate_location(TRUE_LAT, TRUE_LON, 4711)
        app.config["SECRET_KEY"] = "second-map-test-secret"
        second = obfuscate_location(TRUE_LAT, TRUE_LON, 4711)

    assert first != second


def test_offset_stays_within_the_documented_bound(app):
    with app.app_context():
        points = [obfuscate_location(TRUE_LAT, TRUE_LON, i) for i in range(200)]

    assert all(abs(lat - TRUE_LAT) <= 0.005 for lat, _ in points)
    assert all(abs(lon - TRUE_LON) <= 0.005 for _, lon in points)
