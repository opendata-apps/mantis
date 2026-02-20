"""Regression tests for main/public route query handling."""


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
