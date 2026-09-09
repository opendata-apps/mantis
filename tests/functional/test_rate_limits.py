import pytest
from limits.storage import MemoryStorage

from app.extensions import limiter
from tests.helpers import set_client_user


@pytest.fixture
def test_config(test_config):
    class LimitedConfig(test_config):
        RATELIMIT_ENABLED = True

    return LimitedConfig


@pytest.fixture
def limited_client(client):
    assert isinstance(limiter.storage, MemoryStorage)
    limiter.reset()
    yield client
    limiter.reset()


def test_reviewer_url_login_is_limited(limited_client):
    for index in range(10):
        assert limited_client.get(f"/reviewer/invalid-{index}").status_code == 403
    assert limited_client.get("/reviewer/another-guess").status_code == 429


def test_authenticated_reviewer_navigation_is_not_throttled(limited_client):
    set_client_user(limited_client, "9999")
    for _ in range(31):
        assert limited_client.get("/reviewer", follow_redirects=True).status_code == 200


def test_health_probe_has_its_own_limit(limited_client):
    for _ in range(30):
        assert limited_client.get("/health").status_code == 200
    assert limited_client.get("/health").status_code == 429


def test_fourth_report_submission_is_rate_limited(limited_client):
    for _ in range(3):
        assert limited_client.post("/melden", data={}).status_code == 400
    assert limited_client.post("/melden", data={}).status_code == 429
