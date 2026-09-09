"""Application factory behavior through requests and rendered templates."""

from datetime import datetime

from flask import abort, render_template_string
import pytest


@pytest.fixture
def factory_app(app):
    @app.route("/__error/<int:status>")
    def error(status):
        abort(status, description="Request refused")

    return app


def test_flask_app_with_testing_config(factory_app, _db):
    assert factory_app.testing
    response = factory_app.test_client().get("/melden")
    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert 'name="sighting_date"' in response.text


@pytest.mark.parametrize("status", [403, 404, 429])
def test_error_handlers_answer_json_clients(factory_app, status):
    response = factory_app.test_client().get(
        f"/__error/{status}", headers={"Accept": "application/json"}
    )
    assert response.status_code == status
    assert response.get_json() == {"error": "Request refused"}


@pytest.mark.parametrize("status", [403, 404, 429])
def test_error_handlers_answer_browsers(factory_app, status):
    response = factory_app.test_client().get(
        f"/__error/{status}", headers={"Accept": "text/html"}
    )
    assert response.status_code == status
    assert response.mimetype == "text/html"
    assert str(status) in response.text


def test_templates_receive_the_current_time(factory_app):
    before = datetime.now()
    with factory_app.test_request_context():
        rendered = render_template_string("{{ now.isoformat() }}")
    after = datetime.now()

    assert before <= datetime.fromisoformat(rendered) <= after
