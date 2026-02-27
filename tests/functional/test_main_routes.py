"""Regression tests for main/public route query handling."""


def test_health_returns_200_and_healthy(client):
    """The /health endpoint should return JSON with status healthy."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"


class TestMainRouteQueryHandling:
    """Legacy query parameters should not break page rendering."""

    def test_index_ignores_invalid_current_index_param(self, client):
        response = client.get("/?current_index=abc")
        assert response.status_code == 200
        assert b"Gottesanbeterin" in response.data

    def test_galerie_ignores_invalid_current_index_param(self, client):
        with client.session_transaction() as sess:
            sess["user_id"] = "9999"

        response = client.get("/galerie?current_index=abc")
        assert response.status_code == 200
        assert b"gallery-grid" in response.data

    def test_galerie_without_session_returns_403(self, client):
        response = client.get("/galerie")
        assert response.status_code == 403
        html = response.get_data(as_text=True)
        assert "not allowed to access" in html
