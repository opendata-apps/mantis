"""Unit tests for the Vite manifest helpers."""

import pytest

from app.tools import vite


@pytest.fixture
def manifest(monkeypatch):
    """Serve a fixed manifest instead of reading app/static/build."""

    def _install(data):
        monkeypatch.setattr(vite, "_load_manifest", lambda app: data)

    return _install


class TestViteAsset:
    def test_returns_hashed_url(self, app, manifest):
        manifest({"js/map.js": {"file": "map-abc123.js"}})
        with app.test_request_context():
            assert vite.vite_asset("js/map.js") == "/static/build/map-abc123.js"

    def test_missing_entry_is_reported_not_papered_over(self, app, manifest, caplog):
        """A manifest miss means the build is broken.

        Emitting the raw source path instead would serve an ES module with
        unresolvable bare imports — a 200 response and a blank page.
        """
        manifest({})
        with app.test_request_context():
            assert vite.vite_asset("js/map.js") == ""
        assert "js/map.js" in caplog.text

    def test_missing_manifest_is_reported(self, app, manifest, caplog):
        manifest(None)
        with app.test_request_context():
            assert vite.vite_asset("css/theme.css") == ""
        assert "css/theme.css" in caplog.text


class TestViteTags:
    def test_emits_css_script_and_modulepreloads(self, app, manifest):
        manifest(
            {
                "js/map.js": {
                    "file": "map-abc.js",
                    "css": ["map-xyz.css"],
                    "imports": ["_vendor.js"],
                },
                "_vendor.js": {"file": "vendor-def.js"},
            }
        )
        with app.test_request_context():
            html = str(vite.vite_tags("js/map.js"))

        assert '<link rel="stylesheet" href="/static/build/map-xyz.css">' in html
        assert '<script type="module" src="/static/build/map-abc.js"></script>' in html
        assert '<link rel="modulepreload" href="/static/build/vendor-def.js">' in html
        # Stylesheets must precede the entry script
        assert html.index("stylesheet") < html.index("<script")

    def test_missing_entry_emits_nothing_and_logs(self, app, manifest, caplog):
        manifest({})
        with app.test_request_context():
            assert str(vite.vite_tags("js/map.js")) == ""
        assert "js/map.js" in caplog.text
