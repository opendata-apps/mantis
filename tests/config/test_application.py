import flask


def test_app(app):
    assert isinstance(app, flask.Flask)
