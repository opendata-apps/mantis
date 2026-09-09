from flask import has_app_context
from pathlib import Path
import pytest


def test_requests_release_their_application_context(client):
    assert not has_app_context()
    for _ in range(2):
        response = client.get("/")
        assert response.status_code == 200
        assert not has_app_context()


@pytest.mark.parametrize("marker", ["first", "second"])
def test_application_config_is_isolated_between_tests(app, marker):
    leaked_marker = app.config.get("ISOLATION_TEST_MARKER")
    assert leaked_marker is None
    app.config["ISOLATION_TEST_MARKER"] = marker


def test_writable_directories_are_temporary(app, tmp_path):
    for setting in ("UPLOAD_FOLDER", "BACKUP_DIR"):
        assert Path(app.config[setting]).is_relative_to(tmp_path)
