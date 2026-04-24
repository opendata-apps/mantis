"""Smoke tests for the public static-information routes.

These endpoints just render static Jinja templates — no DB-dependent state,
no auth. A handful of older regressions had the blueprint silently broken
when the template path changed; the cheapest guard is a 200-status smoke
test per route.
"""

import pytest


PUBLIC_INFO_ROUTES = [
    "/faq",
    "/impressum",
    "/lizenz",
    "/datenschutz",
    "/bestimmung",
]


@pytest.mark.parametrize("path", PUBLIC_INFO_ROUTES)
def test_public_info_page_renders(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert response.content_type.startswith("text/html")


class TestSitemapAndRobots:
    """The sitemap/robots endpoints cache their bytes at module level.

    Simply comparing two responses' bytes is not enough — identical
    bytes are also what you'd get WITHOUT caching, by re-reading the
    file each time. Instead we spy on ``current_app.open_resource`` and
    assert it is called exactly once across two requests.
    """

    def _reset_caches(self):
        from app.routes import main as main_module

        main_module._sitemap_cache = None
        main_module._robots_cache = None

    def test_sitemap_served_with_xml_mimetype(self, client):
        self._reset_caches()
        response = client.get("/sitemap.xml")
        assert response.status_code == 200
        assert response.content_type.startswith("application/xml")
        assert b"<urlset" in response.data or b"<sitemapindex" in response.data

    def test_sitemap_reads_file_only_on_first_hit(self, app, client):
        self._reset_caches()
        real_open_resource = app.open_resource
        calls = []

        def spy(name, *a, **kw):
            calls.append(name)
            return real_open_resource(name, *a, **kw)

        from unittest.mock import patch

        with patch.object(app, "open_resource", side_effect=spy):
            first = client.get("/sitemap.xml")
            second = client.get("/sitemap.xml")

        # Exactly one file read covering the sitemap across both hits
        sitemap_reads = [c for c in calls if "sitemap" in c]
        assert len(sitemap_reads) == 1, calls
        assert first.data == second.data

    def test_robots_served_as_plain_text(self, client):
        self._reset_caches()
        response = client.get("/robots.txt")
        assert response.status_code == 200
        assert response.content_type.startswith("text/plain")
        # Real robots.txt contains a case-insensitive User-agent line
        assert b"user-agent" in response.data.lower()

    def test_robots_reads_file_only_on_first_hit(self, app, client):
        self._reset_caches()
        real_open_resource = app.open_resource
        calls = []

        def spy(name, *a, **kw):
            calls.append(name)
            return real_open_resource(name, *a, **kw)

        from unittest.mock import patch

        with patch.object(app, "open_resource", side_effect=spy):
            first = client.get("/robots.txt")
            second = client.get("/robots.txt")

        robots_reads = [c for c in calls if "robots" in c]
        assert len(robots_reads) == 1, calls
        assert first.data == second.data


def test_favicon_route_is_registered(app):
    """The ``favicon`` view function is registered under ``/favicon.ico``
    and maps to ``main.favicon``. We don't send an HTTP request because
    the actual file is missing in fresh checkouts (built by Vite) — the
    route contract is what matters here, not the 200/404 response.
    """
    adapter = app.url_map.bind("localhost")
    endpoint, _args = adapter.match("/favicon.ico")
    assert endpoint == "main.favicon"


class TestHealthEndpoint:
    def test_health_unhealthy_on_db_failure(self, client):
        """When the DB is unreachable the endpoint returns 503 with
        ``status: unhealthy`` — this protects the Docker healthcheck from
        silently reporting OK while the app can't serve requests.
        """
        from unittest.mock import patch

        with patch(
            "app.routes.main.db.session.execute",
            side_effect=Exception("db boom"),
        ):
            response = client.get("/health")

        assert response.status_code == 503
        assert response.get_json()["status"] == "unhealthy"


class TestPostCountCache:
    """The home page call site uses a 5-minute TTL cache for the approved
    post count. Resetting the module-level cache lets us verify both
    branches of ``_get_post_count`` — miss and hit.
    """

    def test_cache_hit_reuses_value(self, client):
        from app.routes import main as main_module

        main_module._post_count_cache["value"] = None
        main_module._post_count_cache["timestamp"] = 0

        # First request populates the cache (miss branch)
        first = client.get("/")
        assert first.status_code == 200

        cached_value = main_module._post_count_cache["value"]
        assert cached_value is not None

        # Force the cache branch to be taken by sentinel-swapping the DB
        # session — if the cache fires, no query runs.
        from unittest.mock import patch

        with patch(
            "app.routes.main.db.session.execute",
            side_effect=AssertionError("cache miss — DB hit not expected"),
        ):
            second = client.get("/")
        assert second.status_code == 200
